#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""algorithms.py: Implementação do algoritmo"""

__copyright__ = "Copyright (c) 2021 Isabella Freitas & José Fonseca. MIT. See attached LICENSE.txt file"


from typing import List, Tuple

from numpy import random
from pandas import DataFrame

from two_step_vrptw.utils import Deposito, Cliente, Carro, Frota, Parametros, copia_carro


# ######################################################################################################################
# PAYLOAD


def identifica_clientes_viaveis(frota: Frota, carro: Carro) -> dict:

    # Identificamos a viabilidade de clientes (ainda não atendidos) pela demanda e a carga atual do veiculo
    # Consideramos também se o fim da janela do cliente já passou (para o veículo) - aceleração trivial de seleção
    # Se não existem, retornamos imediatamente
    carga_atual, momento_atual, clientes_atendidos = carro.carga, carro.fim, frota.clientes_atendidos  # SpeedUp Var
    clientes_viaveis = {c: frota[c] for c in frota.clientes_faltantes.difference(carro.clientes_atendidos)}
    clientes_viaveis = {c: v for c, v in clientes_viaveis.items() if v.demanda<=carga_atual and v.fim>momento_atual}
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
        (frota.mapa.matriz_de_distancias[str_clientes_viaveis].loc[posicao_atual] / velocidade).astype(int) + 1
      + DataFrame([[frota[c].inicio + frota[c].servico - frota[c].fim for c in str_clientes_viaveis]],
                  columns=str_clientes_viaveis, index=[posicao_atual])
    ).iloc[0].to_dict()
    return {c: v for c, v in clientes_viaveis.items() if v <= 0}


def calcula_atratividade(parametros: Parametros, frota: Frota, clientes_viaveis: dict, carro: Carro, numero_recursao=0) -> List[Tuple]:

    # Calculamos a atratividade imediata de cada cliente viável
    posicao_atual = str(carro.agenda[-1])
    linha_distancias = frota.mapa.matriz_de_distancias.loc[posicao_atual].to_dict()
    atratividade = {c: sum([
        parametros.peso_distancia * (1.0/linha_distancias[c]),
        (parametros.peso_urgencia * ((frota[c].fim - frota[c].inicio) / abs(v))) if v > 0 else 0.0
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
        carro_recursao.atendimento(frota[cliente])
        sub_clientes_viaveis = identifica_clientes_viaveis(frota, carro_recursao)
        if len(sub_clientes_viaveis) == 0: continue
        sub_atratividade = calcula_atratividade(
            parametros, frota,
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


def _rota_independente(parametros: Parametros, frota: Frota, offset_iteracao: int) -> int:

    # Inicializamos um carro com um deposito qualquer
    carro = frota.novo_carro()

    # Loop principal de execucao:
    for iteracao in range(offset_iteracao, parametros.limite_iteracoes):

        # Identificamos clientes viáveis
        clientes_viaveis = identifica_clientes_viaveis(frota, carro)

        # Se não temos clientes viáveis
        if len(clientes_viaveis) == 0:

            # Se estamos em um cliente, vamos até o depósito e avançamos no loop
            if carro.agenda[-1].tipo == 'Cliente':
                carro.reabastecimento(frota.deposito)
                continue

            # Se estamos em um depósito, retornamos
            else:
                return iteracao

        # Se chegamos até aqui, temos clientes viáveis e podemos continuar. Calculamos a atratividade dos clientes
        atratividade = calcula_atratividade(parametros, frota, clientes_viaveis, carro)

        # Selecionamos randomicamente um cliente viável por roleta
        valor_atratividade = [cli[1] for cli in atratividade]
        valor_atratividade_total = sum(valor_atratividade)
        cliente = random.choice([cli[0] for cli in atratividade], p=[v/valor_atratividade_total for v in valor_atratividade])

        # Avançamos no caminho para o cliente
        carro.atendimento(frota[cliente])

    # Retornamos a iteração máxima, em caso de falha
    return iteracao


def rota_independente(parametros: Parametros, frota: Frota):
    offset_iteracao = 0
    while len(frota.clientes_faltantes) > 0:
        offset_iteracao = _rota_independente(parametros, frota, offset_iteracao)
        if offset_iteracao >= (parametros.limite_iteracoes - 1):
            frota.limpa_carros_sem_agenda()
            return False, parametros.limite_iteracoes
    frota.limpa_carros_sem_agenda()
    return True, offset_iteracao


def rota_coletiva(parametros: Parametros, frota: Frota) -> (bool, int):

    # Inicializamos alguns novos carros
    for _ in range(parametros.qtd_novos_carros_por_rodada):
        frota.novo_carro()

    # Loop principal de execucao:
    for iteracao in range(parametros.limite_iteracoes):

        # Sinalizamos que nessa iteração ainda não houve novo atendimento
        houve_novo_atendimento = False

        # Para cada carro na frota:
        for carro in frota:

            # Identificamos clientes viáveis
            clientes_viaveis = identifica_clientes_viaveis(frota, carro)

            # Se não temos clientes viáveis
            if len(clientes_viaveis) == 0:

                # Se estamos em um cliente, vamos até o depósito e avançamos no loop
                if carro.agenda[-1].tipo == 'Cliente':
                    carro.reabastecimento(frota.deposito)

                # Aqui, o carro tem de estar em um depósito. Assim, finalizamos a iteração
                continue

            # Se chegamos até aqui, temos clientes viáveis e podemos continuar. Calculamos a atratividade dos clientes
            atratividade = calcula_atratividade(parametros, frota, clientes_viaveis, carro)

            # Selecionamos randomicamente um cliente viável por roleta
            valor_atratividade = [cli[1] for cli in atratividade]
            valor_atratividade_total = sum(valor_atratividade)
            cliente = random.choice([cli[0] for cli in atratividade], p=[v/valor_atratividade_total for v in valor_atratividade])

            # Avançamos no caminho para o cliente
            carro.atendimento(frota[cliente])

            # Sinalizamos que nessa iteração houve ao menos um novo atendimento
            houve_novo_atendimento = True

        # Se todos os clientes foram atendidos, retornamos o sucesso
        if len(frota.clientes_faltantes) == 0:
            frota.limpa_carros_sem_agenda()
            return True, iteracao

        # Se, após iterar todos os carros, não tivemos nenhum atendimento, acrescentamos novos carros
        if not houve_novo_atendimento:
            for _ in range(parametros.qtd_novos_carros_por_rodada):
                frota.novo_carro()

    # Retornamos a iteração máxima, em caso de falha
    frota.limpa_carros_sem_agenda()
    return False, iteracao


def gera_solucao(parametros:Parametros, frota:Frota, tipo='rota_independente') -> (bool, int):

    if tipo == 'rota_independente':
        return rota_independente(parametros, frota)

    elif tipo == 'rota_coletiva':
        return rota_coletiva(parametros, frota)

    else:
        raise NotImplementedError(f'Tipo nao implementado: {tipo}')
