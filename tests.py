#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests.py: Testes de unidade da implementação do algoritmo"""

__copyright__ = "Copyright (c) 2021 Isabella Freitas & José Fonseca. MIT. See attached LICENSE.txt file"


import sys
import timeit
from pprint import pprint
from two_step_vrptw.utils import Frota, Parametros, Mapa
from two_step_vrptw import algorithms


def time_it(nome, qtd_repeticoes, funcao):
    print(nome, '\t', round(timeit.timeit(funcao, number=qtd_repeticoes) / qtd_repeticoes * 1000, 3), f'(ms) |{qtd_repeticoes}|')


if __name__ == '__main__':
    TO_TIME = ('--time' in sys.argv)

    parametros = Parametros(
        peso_distancia    = 5.0,    # 5.0,
        peso_urgencia     = 0.165,  # 0.165,
        peso_recursoes    = 2.0,    # 2.0
        limite_recursoes  = 3,      # 3
        clientes_recursao = 4,      # 5
        limite_iteracoes = 1000
    )

    if ('parse' in sys.argv):
        if TO_TIME:
            time_it('PARSE ARQUIVO', 2000, lambda: Mapa.parse_arquivo('data/solomon_1987/r2/r201.txt'))
        else:
            nome_teste, max_carros, capacidade_carro, deposito, clientes = Mapa.parse_arquivo('data/solomon_1987/r2/r201.txt')
            print(nome_teste, max_carros, capacidade_carro)
            print(deposito)
            for cli in clientes:
                print('\t', cli)

    if ('matriz' in sys.argv):
        if TO_TIME:
            nome_teste, max_carros, capacidade_carro, deposito, clientes = Mapa.parse_arquivo('data/solomon_1987/r2/r201.txt')
            time_it('CRIA MATRIZ', 20, lambda: Mapa.cria_matriz_de_distancias(deposito, clientes))
        else:
            nome_teste, max_carros, capacidade_carro, deposito, clientes = Mapa.parse_arquivo('data/solomon_1987/r2/r201.txt')
            df_distancias, dict_referencias = Mapa.cria_matriz_de_distancias(deposito, clientes)
            pprint(df_distancias)

    if ('mapa' in sys.argv):
        if TO_TIME:
            time_it('CRIA MAPA', 20, lambda: Mapa('data/solomon_1987/r2/r201.txt'))
        else:
            mapa = Mapa('data/solomon_1987/r2/r201.txt')
            pprint(mapa)
            pprint(mapa.dict_referencias)

    if ('frota' in sys.argv):
        if TO_TIME:
            mapa = Mapa('data/solomon_1987/r2/r201.txt')
            time_it('CRIA FROTA[]', 5, lambda: Frota(mapa, 1))
        else:
            mapa = Mapa('data/solomon_1987/r2/r201.txt')
            frota = Frota(mapa, 1)
            pprint(frota)

    if ('carro' in sys.argv):
        if TO_TIME:
            mapa = Mapa('data/solomon_1987/r2/r201.txt')
            frota = Frota(mapa, 1)
            time_it('CRIA CARRO', 10, lambda: frota.novo_carro())
        else:
            mapa = Mapa('data/solomon_1987/r2/r201.txt')
            frota = Frota(mapa, 1)
            pprint(frota.novo_carro())

    if ('identifica_clientes_viaveis' in sys.argv):
        if TO_TIME:
            mapa = Mapa('data/solomon_1987/r2/r201.txt')
            frota = Frota(mapa, 1)
            carro = frota.novo_carro()
            time_it('IDENTIFICA CLIENTES VIAVEIS', 200, lambda: algorithms.identifica_clientes_viaveis(frota, carro))
        else:
            mapa = Mapa('data/solomon_1987/r2/r201.txt')
            frota = Frota(mapa, 1)
            carro = frota.novo_carro()
            pprint(algorithms.identifica_clientes_viaveis(frota, carro))

    if ('calcula_atratividade' in sys.argv):
        if TO_TIME:
            mapa = Mapa('data/solomon_1987/r2/r201.txt')
            frota = Frota(mapa, 1)
            carro = frota.novo_carro()
            clientes_viaveis = algorithms.identifica_clientes_viaveis(frota, carro)
            time_it('CALCULA_ATRATIVIDADE', 10, lambda: algorithms.calcula_atratividade(parametros, frota, clientes_viaveis, carro))
        else:
            mapa = Mapa('data/solomon_1987/r2/r201.txt')
            frota = Frota(mapa, 1)
            carro = frota.novo_carro()
            clientes_viaveis = algorithms.identifica_clientes_viaveis(frota, carro)
            pprint(algorithms.calcula_atratividade(parametros, frota, clientes_viaveis, carro))

    if ('rota_independente' in sys.argv):
        if TO_TIME:
            mapa = Mapa('data/solomon_1987/r2/r201.txt')
            frota = Frota(mapa, 1)
            time_it('UMA ROTA INDEPENDENTE', 10, lambda: algorithms.rota_independente(parametros, frota))
        else:
            mapa = Mapa('data/solomon_1987/r2/r201.txt')
            frota = Frota(mapa, 1)
            carro = algorithms.rota_independente(parametros, frota)
            pprint(frota)
            pprint(carro)

    if ('independente' in sys.argv) or ('individual' in sys.argv):
        if TO_TIME:
            mapa = Mapa('data/solomon_1987/r2/r201.txt')
            frota = Frota(mapa, 1)
            time_it('SOLUCAO POR ROTA INDEPENDENTE', 10, lambda: algorithms.gera_solucao(parametros, frota, tipo='rota_independente'))
            sumario = frota.sumario
            print(frota)
            print('Inicio:', sumario['inicio'].min(), 'Fim:', sumario['fim'].max(),
                  'Distancia:', round(sumario['distancia'].sum(), 3), 'T.Atividade', sumario['tempo_atividade'].sum(),
                  'Tempo Total:', sumario['fim'].sum(),
                  'T.Deslocamento:', sumario['tempo_deslocamento'].sum(), 'T.Layover:', sumario['tempo_layover'].sum())
        else:
            mapa = Mapa('data/solomon_1987/r2/r201.txt')
            frota = Frota(mapa, 1)
            result = algorithms.gera_solucao(parametros, frota, tipo='rota_independente')
            sumario = frota.sumario
            print(frota, result)
            print('Inicio:', sumario['inicio'].min(), 'Fim:', sumario['fim'].max(),
                  'Distancia:', round(sumario['distancia'].sum(), 3), 'T.Atividade', sumario['tempo_atividade'].sum(),
                  'Tempo Total:', sumario['fim'].sum(),
                  'T.Deslocamento:', sumario['tempo_deslocamento'].sum(), 'T.Layover:', sumario['tempo_layover'].sum())
            pprint(sumario)
            frota.carros['0'].resultado()

    if ('coletiva' in sys.argv):
        if TO_TIME:
            mapa = Mapa('data/solomon_1987/r2/r201.txt')
            frota = Frota(mapa, 1)
            time_it('SOLUCAO POR ROTA COLETIVA', 10, lambda: algorithms.gera_solucao(parametros, frota, tipo='rota_coletiva'))
            sumario = frota.sumario
            print(frota)
            print('Inicio:', sumario['inicio'].min(), 'Fim:', sumario['fim'].max(),
                  'Distancia:', round(sumario['distancia'].sum(), 3), 'T.Atividade', sumario['tempo_atividade'].sum(),
                  'Tempo Total:', sumario['fim'].sum(),
                  'T.Deslocamento:', sumario['tempo_deslocamento'].sum(), 'T.Layover:', sumario['tempo_layover'].sum())
        else:
            mapa = Mapa('data/solomon_1987/r2/r201.txt')
            frota = Frota(mapa, 1)
            result = algorithms.gera_solucao(parametros, frota, tipo='rota_coletiva')
            sumario = frota.sumario
            print(frota, result)
            print('Inicio:', sumario['inicio'].min(), 'Fim:', sumario['fim'].max(),
                  'Distancia:', round(sumario['distancia'].sum(), 3), 'T.Atividade', sumario['tempo_atividade'].sum(),
                  'Tempo Total:', sumario['fim'].sum(),
                  'T.Deslocamento:', sumario['tempo_deslocamento'].sum(), 'T.Layover:', sumario['tempo_layover'].sum())
            pprint(sumario)
            frota.carros['0'].resultado()
