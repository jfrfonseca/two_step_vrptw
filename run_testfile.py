#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests.py: Testes de unidade da implementação do algoritmo"""

__copyright__ = "Copyright (c) 2021 Isabella Freitas & José Fonseca. MIT. See attached LICENSE.txt file"


import os
import sys
import pickle
from time import time
from two_step_vrptw.utils import Frota, Parametros, Mapa
from two_step_vrptw import algorithms



if __name__ == '__main__':

    try:
        mapa = Mapa(sys.argv[1])
    except AssertionError as ass:
        print(ass)
        sys.exit(0)
    for p_dist, p_urg, p_rec in zip([2,    5,     7],
                                    [0.12, 0.165, 0.20],
                                    [0.5,  1.0,   2.0]):
        for rep in range(10):
            dire = sys.argv[1].split('/')
            nome_arq = f'results/{dire[-2]}/'+'_'.join(map(str, [p_dist, p_urg, p_rec, rep, dire[-1]]))+'.pkl'
            pathway = '/'.join(nome_arq.split('/')[:-1])
            if not os.path.exists(pathway):
                os.makedirs(pathway)
            if os.path.exists(nome_arq): continue
            begin = time()
            result = {}
            parametros = Parametros(
                peso_distancia=p_dist,
                peso_urgencia=p_urg,
                peso_recursoes=p_rec,
                limite_recursoes=3,
                clientes_recursao=4,
                limite_iteracoes=10000
            )
            print(rep, parametros)
            frota = Frota(mapa, 1)
            validade, iteracoes = algorithms.gera_solucao(parametros, frota, tipo='rota_independente')
            print(frota, validade, iteracoes)
            result['frota_pre_opt'] = str(frota)
            if validade:
                result['sumario_pre_opt'] = frota.sumario.copy()
                algorithms.otimizacao_termino_mais_cedo(frota)
                print(frota)
                result['sumario'] = frota.sumario.copy()
            elif rep > 2:
                print('Arquivo com tempo de servico invalido')
                sys.exit(0)

            result.update({
                'begin': begin, 'end': time(), 'arquivo': sys.argv[1],
                'frota': frota, 'iteracoes': iteracoes, 'validade': validade, 'parametros': parametros
            })
            with open(nome_arq, 'wb') as fout:
                pickle.dump(result, fout)
