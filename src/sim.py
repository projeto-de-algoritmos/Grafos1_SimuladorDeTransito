import json
from enum import Enum
import traceback

from .geometry import *
from .gui import *
from .const import *


def dprint(*values: object):
    if DEBUG:
        print("[DEBUG]", *values)


def eprint(*values: object, cexit=True):
    traceback.print_stack()
    print("[ERROR]", *values)
    if cexit:
        exit(1)


def enum_list(values: list[Enum]):
    r = []
    for value in values:
        r.append(value.name)
    return sorted(r)


cor = tuple[int, int, int]

Direcao = Enum("Direcao", "normal contrario")
FaixaTipo = Enum("FaixaTipo", "acostamento geral")


class Faixa:
    pista: "Pista"
    tipo: FaixaTipo
    sentido: Direcao

    def __init__(self, tipo: FaixaTipo, sentido: Direcao):
        self.tipo = FaixaTipo(tipo)
        self.sentido = Direcao(sentido)


class Pista:
    p1: point
    p2: point
    faixas: list[Faixa]
    carros: list["Carro"]

    def __init__(
        self, p1: point, p2: point, faixas: list[Faixa], carros: list["Carro"]
    ):
        self.p1 = p1
        self.p2 = p2
        self.faixas = faixas
        for faixa in self.faixas:
            faixa.pista = self
        self.carros = carros
        for carro in self.carros:
            carro.pista = self
            carro.faixa = self.faixas[carro.faixa_i]

    def get_comprimento(self):
        return distancia_euclidiana(self.p1, self.p2)


class Carro:
    pista: Pista
    faixa: Faixa
    pista_i: int
    faixa_i: int

    nome: str
    cor: str = "#FF0000"
    posicao: float
    velocidade: float
    destino: point
    velocidade_relativa_maxima_aceitavel: float

    # currently unused
    aceleracao: float

    def __init__(
        self,
        pista_i: int,
        faixa_i: int,
        nome: str,
        cor: str,
        posicao: float,
        velocidade: float,
        destino: point,
        max_rvel: float,
        aceleracao: float,
    ):
        self.nome = nome
        self.cor = cor
        self.pista_i = pista_i
        self.faixa_i = faixa_i
        self.posicao = posicao
        self.velocidade = velocidade
        self.destino = destino
        self.max_rvel = max_rvel
        self.aceleracao = aceleracao


class Simulation:
    pistas: list[Pista]
    carros: dict[str, Carro]

    running: bool = False

    tick_rate: int

    def __init__(self, cenario_file, tick_rate=60):
        pistas, carros = self.read(cenario_file)
        self.pistas = pistas
        self.carros = carros

        self.running = True

        self.tick_rate = tick_rate

    def get_pistas_and_carros(self):
        return self.pistas

    def read(self, cenario_file):
        data = self.read_and_parse_json_file(cenario_file)

        pistas = []
        carros: dict[str, Carro] = {}

        for carro in data["carros"]:
            nome = carro["nome"]

            carro_obj = Carro(
                nome=nome,
                cor=carro["cor"],
                pista_i=carro["pista"],
                faixa_i=carro["faixa"],
                posicao=carro["posicao"],
                velocidade=carro["velocidade"],
                destino=carro["destino"],
                max_rvel=carro["max_rvel"],
                aceleracao=carro["aceleracao"],
            )

            if carros.get(nome) is not None:
                eprint(f"Carro {nome} já existe!")

            carros[nome] = carro_obj

        for i in range(len(data["pistas"])):
            pista = data["pistas"][i]
            faixas = []
            for faixa in pista["faixas"]:
                faixa_obj = Faixa(FaixaTipo[faixa["tipo"]], Direcao[faixa["sentido"]])
                faixas.append(faixa_obj)

            pista_carros = list(
                filter(lambda carro: i == carro.pista_i, carros.values())
            )

            pista = Pista(
                p1=pista["p1"], p2=pista["p2"], faixas=faixas, carros=pista_carros
            )

            pistas.append(pista)

        return pistas, carros

    def read_and_parse_json_file(self, path):
        with open(path, "r") as f:
            data = json.load(f)
            return data

    def jump_to_next_tick(self):
        pass

    def update(self):
        for carro in self.carros.values():
            carro.posicao += carro.velocidade / self.tick_rate
            if carro.posicao > carro.pista.get_comprimento() - COMPRIMENTO_CARRO:
                carro.posicao = 0
