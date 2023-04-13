import pygame
import datetime
import time
import json
from enum import Enum
import traceback

DEBUG = True
def dprint(*values: object):
    print("[DEBUG]", *values)

def eprint(*values: object):
    traceback.print_stack()
    print("[ERROR]", *values)

def enum_list(values: Enum):
    r = []
    for value in values:
        r.append(value.name)
    return sorted(r)

point = list[int, int]
cor = tuple[int, int, int]

Direcao = Enum('Direcao', "leste oeste norte sul parado")
FaixaTipo = Enum('FaixaTipo', "acostamento geral")

COR_ACOSTAMENTO = (30, 30, 30)
COR_FAIXA = (15, 15, 15)
COR_DIVISORIA_FAIXA_SENTIDO_IGUAL = (200, 200, 200)
COR_DIVISORIA_FAIXA_SENTIDO_DIFERENTE = (200, 200, 0)
COR_DIVISORIA_FAIXA_ACOSTAMENTO = (160, 160, 160)

LARGURA_DIVISORIA = 2


class DrawItem():
    def __init__(self):
        pass

    def draw(self, scr: pygame.Surface):
        eprint("FAILED TO IMPLEMENT DRAW")
        exit(1)


class Drawer():
    x: int = 0
    draw_items: list[DrawItem]

    def __init__(self, draw_items: list[DrawItem] = []):
        self.draw_items = draw_items

    def draw(self, scr: pygame.Surface):
        scr.fill((255, 255, 255))

        for draw_item in self.draw_items:
            draw_item.draw(scr)

        pygame.display.flip()


class GUI():
    MAX_FPS = 60
    SEC_IN_MICROSECONDS = 10e6
    STEP_TIME = SEC_IN_MICROSECONDS / MAX_FPS

    scr: pygame.Surface = None
    running = False
    drawer = None

    def __init__(self, drawer: Drawer = Drawer()):
        pygame.init()
        self.scr = pygame.display.set_mode((600, 500))
        self.running = True
        self.drawer = drawer

    def run(self):
        while self.running:
            ti = datetime.datetime.now()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.drawer.draw(self.scr)

            diff = datetime.datetime.now() - ti
            diff = diff.microseconds

            if self.STEP_TIME > diff:
                wait_time = (self.STEP_TIME - diff) / self.SEC_IN_MICROSECONDS
                time.sleep(wait_time)

    def exit():
        pygame.quit()


class Faixa():
    tipo: FaixaTipo
    direcao_de_movimento: Direcao
    sentido: Direcao

    def __init__(self, tipo: FaixaTipo, relativo: Direcao, sentido: Direcao):
        self.tipo = FaixaTipo(tipo)
        self.relativo = Direcao(relativo)
        self.sentido = Direcao(sentido)


class Pista():
    p1: point
    p2: point
    direcao: Direcao
    faixas: list[Faixa]
    step_w: int = None

    def __init__(self, p1: point, p2: point, direcao: Direcao, faixas: list[Faixa]):
        self.p1 = p1
        self.p2 = p2
        self.direcao = direcao
        self.faixas = faixas


def rect(p1: point, p2: point):
    x = min(p1[0], p2[0])
    y = min(p1[1], p2[1])
    w = max(p1[0], p2[0]) - x
    h = max(p1[1], p2[1]) - y
    return (x, y, w, h)


def get_params_directional_rect(p1: point, p2: point, direcao: Direcao, dlt: float):
    x: float
    y: float
    w: float
    h: float

    if direcao == Direcao["leste"] or direcao == Direcao["oeste"]:
        x, y, w, h = rect(
            [p1[0], p1[1] + dlt], [p2[0], p2[1] + dlt]
        )
    else:
        x, y, w, h = rect(
            [p1[0] + dlt, p1[1]], [p2[0] + dlt, p2[1]]
        )

    return (x, y, w, h)


class PistaDrawer(DrawItem):
    pista: Pista = None

    def __init__(self, pista: Pista):
        self.pista = pista

    def draw(self, scr: pygame.Surface):
        last_faixa = None
        dlt = 0
        for faixa in self.pista.faixas:
            if last_faixa is not None:
                dlt = dlt + \
                    self.draw_divisoria(
                        dlt, scr, last_faixa, faixa, self.pista.direcao)

            dlt = dlt = self.draw_faixa(dlt, scr, faixa)

            last_faixa = faixa

    def get_cor_divisoria(self, faixa_anterior: Faixa, faixa_proxima: Faixa) -> cor:
        tipos = enum_list([faixa_anterior.tipo, faixa_proxima.tipo])
        if tipos == ["acostamento", "geral"]:
            dprint(1)
            return COR_DIVISORIA_FAIXA_ACOSTAMENTO
        elif tipos == ["acostamento", "acostamento"]:
            dprint(2)
            eprint("acostamento seguido de acostamento")
            exit(1)
        elif faixa_anterior.tipo == faixa_proxima.tipo:
            dprint(3)
            return COR_DIVISORIA_FAIXA_SENTIDO_IGUAL
        elif faixa_anterior.sentido != faixa_anterior.sentido:
            dprint(4)
            return COR_DIVISORIA_FAIXA_SENTIDO_DIFERENTE
        else:
            dprint(5)
            eprint("Tipo de faixa irreconhecivel: " +
                  str(faixa_anterior.tipo) + " " + str(faixa_proxima.tipo))
            exit(1)

    def draw_divisoria(self,  dlt: float, scr: pygame.Surface, faixa_anterior: Faixa, faixa_proxima: Faixa, direcao: Direcao) -> float:
        cor = self.get_cor_divisoria(faixa_anterior, faixa_proxima)

        dlt = dlt + LARGURA_DIVISORIA
        rect = get_params_directional_rect(
            faixa_anterior.p1, faixa_anterior.p2, direcao, dlt)

        pygame.draw.rect(scr, cor, rect)

        return dlt

    def draw_faixa(self, dlt: float, scr: pygame.Surface, faixa: Faixa) -> float:
        cor = COR_FAIXA
        if faixa.tipo == FaixaTipo["acostamento"]:
            cor = COR_ACOSTAMENTO

        # botar setas pra indicar direção?

        rect = get_params_directional_rect(
            self.pista.p1, self.pista.p2, faixa.sentido, dlt)

        pygame.draw.rect(scr, cor, rect)


def read_and_parse_json_file(path="config.json"):
    with open(path, "r") as f:
        data = json.load(f)
        return data


def execute():
    data = read_and_parse_json_file()

    pistas = []

    for pista in data["pistas"]:
        faixas = []
        for faixa in pista["faixas"]:
            faixa_obj = Faixa(
                FaixaTipo[faixa["tipo"]], Direcao[faixa["relativo"]], Direcao[faixa["sentido"]])
            faixas.append(faixa_obj)

        pista = Pista(
            p1=pista["p1"],
            p2=pista["p2"],
            direcao=Direcao[pista["direcao"]],
            faixas=faixas
        )

        pistas.append(pista)

    gui = GUI(Drawer([PistaDrawer(pista)]))
    gui.run()


if __name__ == '__main__':
    execute()
