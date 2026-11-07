"""Equipamentos originais do quiosque. Blender Z-up; frente em -Y (Godot +Z).
Porta exportada separadamente com origem na dobradiça, vidro translúcido e puxador.
"""
from gen_code_props import fresh, mat, box, export
from gen_food import _glass_mat
import math


def fridge():
    fresh()
    white = mat('esmalte_gelo', (0.84, 0.92, 0.89), .3, metal=.15)
    inside = mat('interior_verde', (.09, .23, .22), .55)
    steel = mat('aco_prateleiras', (.57, .66, .66), .3, metal=.7)
    box((.95, .06, 1.85), (0, .29, .925), inside)
    for x in [-.45, .45]:
        box((.05, .62, 1.85), (x, 0, .925), white)
    for z in [.045, 1.805]:
        box((.95, .62, .09), (0, 0, z), white)
    for z in [.30, .78, 1.26]:
        box((.85, .54, .025), (0, -.015, z), steel, .006)
        box((.85, .025, .035), (0, -.28, z), white, .006)
    box((.84, .04, .12), (0, -.30, 1.7), white)
    for x in [-.3, .3]:
        box((.12, .42, .05), (x, 0, .025), steel)
    export('service_fridge')


def door():
    fresh()
    rim = mat('moldura_porta', (.68, .79, .77), .25, metal=.5)
    dark = mat('borracha_vedacao', (.035, .055, .05), .9)
    glass = _glass_mat('vidro_transparente_geladeira', .14)
    for x in [.025, .925]:
        box((.05, .04, 1.85), (x, 0, .925), rim)
    for z in [.025, 1.825]:
        box((.95, .04, .05), (.475, 0, z), rim)
    box((.85, .012, 1.73), (.475, 0, .925), glass, .001)
    for z in [.55, 1.12]:
        box((.035, .09, .035), (.85, -.06, z), dark)
    box((.04, .05, .61), (.85, -.12, .835), rim)
    export('service_fridge_door')


def cabinet():
    fresh()
    wood = mat('madeira_cozinha', (.48, .25, .12), .65)
    cream = mat('laminado_lavavel', (.88, .86, .73), .4)
    box((1.1, .05, 1.3), (0, .29, .65), wood)
    for x in [-.525, .525]:
        box((.05, .62, 1.3), (x, 0, .65), wood)
    for z in [.04, .39, .74, 1.27]:
        box((1.1, .62, .045), (0, 0, z), cream)
    for x in [-.48, .48]:
        box((.07, .5, .06), (x, .01, .03), wood)
    export('service_food_cabinet')


def register():
    fresh()
    dark = mat('terminal_azul', (.035, .14, .16), .35)
    screen = mat('tela_caixa', (.14, .65, .59), .2)
    key = mat('teclas_creme', (.84, .88, .80), .5)
    box((.30, .30, .055), (0, 0, .0275), dark, .015)
    box((.06, .06, .13), (0, .06, .10), dark)
    box((.28, .045, .18), (0, .035, .205), dark, .012, rot=(math.radians(15), 0, 0))
    box((.24, .012, .135), (0, .004, .205), screen, .004, rot=(math.radians(15), 0, 0))
    for x in [-.08, 0, .08]:
        for y in [-.10, -.055]:
            box((.045, .028, .008), (x, y, .060), key, .004)
    export('service_register')


if __name__ == '__main__':
    fridge()
    door()
    cabinet()
    register()
