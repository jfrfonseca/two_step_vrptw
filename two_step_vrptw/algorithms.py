#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""algorithms.py: Implementação do algoritmo"""

__copyright__ = "Copyright (c) 2021 Isabella Freitas & José Fonseca. MIT. See attached LICENSE.txt file"


from typing import List, Tuple

from pandas import DataFrame
from numpy import power, sqrt, random

from two_step_vrptw.utils import Deposito, Cliente, Carro, Parametros, copia_carro


# ######################################################################################################################
# PAYLOAD


def cria_matriz_de_distancias(deposito: Deposito, clientes: List[Cliente]) -> (DataFrame, dict):
    lista_referencia = [deposito]+clientes
    str_lista_referencia = list(map(str, lista_referencia))

    # Calculamos as distancias entre cada ponto no mapa
    df_x = DataFrame([[i.x for i in lista_referencia]]*len(lista_referencia),
                     columns=str_lista_referencia, index=str_lista_referencia)
    df_x = (df_x - df_x.T).applymap(lambda x: power(x, 2))
    df_y = DataFrame([[i.y for i in lista_referencia]]*len(lista_referencia),
                     columns=str_lista_referencia, index=str_lista_referencia)
    df_y = (df_y - df_y.T).applymap(lambda y: power(y, 2))
    df_distancias = (df_x + df_y).applymap(sqrt).astype(float).round(3)

    return df_distancias, dict(zip(str_lista_referencia, lista_referencia))


def identifica_clientes_viaveis(dict_referencias: dict, matriz_de_distancias: DataFrame, carro: Carro) -> dict:

    # Identificamos a viabilidade de clientes (ainda não atendidos) pela demanda e a carga atual do veiculo
    # Consideramos também se o fim da janela do cliente já passou (para o veículo) - aceleração trivial de seleção
    # Se não existem, retornamos imediatamente
    carga_atual, momento_atual, clientes_atendidos = carro.carga, carro.fim, carro.clientes_atendidos  # SpeedUp Var
    clientes_viaveis = {c: v for c, v in dict_referencias.items()
                        if all([v.demanda <= carga_atual,
                                v.fim > momento_atual,
                                c not in clientes_atendidos,
                                not c.startswith('DEPOSITO')])}
    if len(clientes_viaveis) == 0: return {}

    # Computamos a viabilidade de cada cliente selecionado na etapa anterior
    # Calculamos o de tempo de deslocamento do veiculo para cada cliente
    # Somamos com o tempo de servico em cada cliente
    # Somamos com a hora de inicio da janela de atendimento em cada cliente
    # Subtraimos a hora de fim da janela de atendimento em cada cliente
    # Queremos apenas os resultados que não sejam positivos
    # Desses, identificamos a atratividade
    str_clientes_viaveis = list(clientes_viaveis.keys())  # Speedup de acesso de variável
    posicao_atual, velocidade = str(carro.agenda[-1]), carro.velocidade  # SpeedUp de acesso de variável
    clientes_viaveis = (
        (matriz_de_distancias[str_clientes_viaveis].loc[posicao_atual] / velocidade).astype(int) + 1
      + DataFrame([[dict_referencias[c].inicio + dict_referencias[c].servico - dict_referencias[c].fim
                    for c in str_clientes_viaveis]],
                  columns=str_clientes_viaveis, index=[posicao_atual])
    ).iloc[0].to_dict()
    return {c: v for c, v in clientes_viaveis.items() if v <= 0}


def calcula_atratividade(parametros: Parametros, dict_referencias: dict, matriz_de_distancias: DataFrame,
                         clientes_viaveis: dict, carro: Carro, numero_recursao=0) -> List[Tuple]:

    # Calculamos a atratividade imediata de cada cliente viável
    posicao_atual = str(carro.agenda[-1])
    linha_distancias = matriz_de_distancias.loc[posicao_atual].to_dict()
    atratividade = {c: sum([
        parametros.peso_distancia * (1.0/linha_distancias[c]),
        (parametros.peso_urgencia * ((dict_referencias[c].fim - dict_referencias[c].inicio) / abs(v))) if v > 0 else 0.0
    ]) for c, v in clientes_viaveis.items()}

    # Selecionamos apenas os clientes viáveis de maior atratividade
    atratividade = sorted(atratividade.items(), key=lambda par: -1*par[1])[:parametros.clientes_recursao]

    # Se não temos mais recursões, retornamos imediatamente
    if numero_recursao >= parametros.limite_recursoes: return atratividade

    # Se chegamos até aqui, temos pelo menos mais um nivel de recursão
    atratividade = dict(atratividade)
    for cliente, atratividade_cliente in atratividade.items():

        # Geramos um carro simulado para a recursão e calculamos a atratividade dos clientes depois do atual
        carro_recursao = copia_carro(carro)
        carro_recursao.atendimento(dict_referencias[cliente])
        sub_clientes_viaveis = identifica_clientes_viaveis(dict_referencias, matriz_de_distancias, carro_recursao)
        if len(sub_clientes_viaveis) == 0: continue
        sub_atratividade = calcula_atratividade(
            parametros, dict_referencias, matriz_de_distancias,
            sub_clientes_viaveis, carro_recursao,
            numero_recursao=numero_recursao+1
        )
        if len(sub_atratividade) == 0: continue

        # Somamos a atratividade dos clientes depois do atual no cliente atual
        atratividade[cliente] = atratividade_cliente + (
            parametros.peso_recursoes * (sum([i[1] for i in sub_atratividade]) / len(sub_atratividade))
        )

    # Retornamos a atratividade compensada
    return sorted(atratividade.items(), key=lambda par: -1*par[1])[:parametros.clientes_recursao]


def rota_independente(parametros: Parametros, dict_referencias: dict, matriz_de_distancias: DataFrame,
                      deposito:Deposito, capacidade: float, velocidade: int) -> Carro:

    # Inicializamos um carro com um deposito qualquer
    carro = Carro(origem=deposito, capacidade=capacidade, velocidade=velocidade)

    # Loop principal de execucao:
    for iteracao in range(parametros.limite_iteracoes):

        # Identificamos clientes viáveis
        clientes_viaveis = identifica_clientes_viaveis(dict_referencias, matriz_de_distancias, carro)

        # Se não temos clientes viáveis
        if len(clientes_viaveis) == 0:

            # Se estamos em um cliente, vamos até o depósito e avançamos no loop
            if carro.agenda[-1].tipo == 'Cliente':
                carro.reabastecimento(deposito)
                continue

            # Se estamos em um depósito, retornamos
            else:
                return carro

        # Se chegamos até aqui, temos clientes viáveis e podemos continuar. Calculamos a atratividade dos clientes
        atratividade = calcula_atratividade(parametros, dict_referencias, matriz_de_distancias, clientes_viaveis, carro)

        # Selecionamos randomicamente um cliente viável por roleta
        valor_atratividade = [cli[1] for cli in atratividade]
        valor_atratividade_total = sum(valor_atratividade)
        cliente = random.choice([cli[0] for cli in atratividade], p=[v/valor_atratividade_total for v in valor_atratividade])

        # Avançamos no caminho para o cliente
        carro.atendimento(dict_referencias[cliente])
