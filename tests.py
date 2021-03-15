#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests.py: Testes de unidade da implementação do algoritmo"""

__copyright__ = "Copyright (c) 2021 Isabella Freitas & José Fonseca. MIT. See attached LICENSE.txt file"


import timeit
from pprint import pprint
from two_step_vrptw.utils import le_mapa, Carro, Parametros
from two_step_vrptw.algorithms import cria_matriz_de_distancias, identifica_clientes_viaveis, calcula_atratividade
from two_step_vrptw.algorithms import rota_independente


if __name__ == '__main__':

    parametros = Parametros(
        peso_distancia    = 5.0,    # 5.0,
        peso_urgencia     = 0.165,  # 0.165,
        peso_recursoes    = 2.0,    # 2.0
        limite_recursoes  = 3,      # 4
        clientes_recursao = 5       # 5
    )

    nome_teste, max_carros, capacidade_carro, deposito, clientes = le_mapa('data/solomon_1987/r2/r201.txt')
    print(nome_teste, max_carros, capacidade_carro)
    print(deposito)
    # for cli in clientes:
    #     print('\t', cli)

    df_distancias, dict_referencias = cria_matriz_de_distancias(deposito, clientes)
    # pprint(df_distancias)

    # carro = Carro(origem=deposito, capacidade=capacidade_carro, velocidade=1)
    # print(carro)

    # qtd_repeticoes = 200
    # print('CLIENTES VIAVEIS', '(ms)', '=>',
    #       round(timeit.timeit(lambda: identifica_clientes_viaveis(dict_referencias, df_distancias, carro),
    #                           number=qtd_repeticoes) / qtd_repeticoes * 1000, 3))
    # clientes_viaveis = identifica_clientes_viaveis(dict_referencias, df_distancias, carro)
    # pprint(clientes_viaveis)

    # qtd_repeticoes = 20
    # print('ATRATIVIDADE', '(ms)', '=>',
    #       round(timeit.timeit(lambda: calcula_atratividade(parametros, dict_referencias, df_distancias, clientes_viaveis, carro),
    #                           number=qtd_repeticoes) / qtd_repeticoes * 1000, 3))
    # atratividade = calcula_atratividade(parametros, dict_referencias, df_distancias, clientes_viaveis, carro)
    # pprint(atratividade)

    qtd_repeticoes = 20
    print('ATRATIVIDADE', '(ms)', '=>',
          round(timeit.timeit(lambda: rota_independente(parametros, dict_referencias, df_distancias, deposito, capacidade_carro, velocidade=1),
                              number=qtd_repeticoes) / qtd_repeticoes * 1000, 3))
    # carro = rota_independente(parametros, dict_referencias, df_distancias, deposito, capacidade_carro, velocidade=1)
    # carro.display()
