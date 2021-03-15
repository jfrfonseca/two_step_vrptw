#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""objetos.py: Objetos e utilidades necessários para a implementação do algoritmo"""

__copyright__ = "Copyright (c) 2021 Isabella Freitas & José Fonseca. MIT. See attached LICENSE.txt file"


from math import sqrt
from sys import maxsize as int_inf
from typing import List, Tuple, Union
from dataclasses import dataclass, field
from functools import lru_cache as memoized


# ######################################################################################################################
# DATA CLASSES


@dataclass(frozen=True)
class Posicao(object):
    x:  float
    y:  float

    def __repr__(self): return f'({self.x}, {self.y})'
    def __str__(self): return self.__repr__()

    # @memoized(maxsize=100)  # TODO: Verificar a pegada de memória antes de ativar memoização!
    def distancia(self, outro) -> float:
        return round(sqrt(float(self.x-outro.x)**2 + float(self.y-outro.y)**2), 3)


@dataclass(frozen=True)
class Cliente(Posicao):
    demanda: float
    inicio:  int
    fim:     int
    servico: int
    tipo = 'Cliente'

    def __repr__(self): return f'CLIENTE({self.demanda} ({self.x}, {self.y}) [{self.inicio}, {self.fim}] {self.servico})'


@dataclass(frozen=True)
class Deposito(Posicao):
    demanda = 0.0
    inicio = 0
    fim = int_inf
    servico = 0.0
    tipo = 'Depósito'

    def __repr__(self): return f'DEPOSITO({self.x}, {self.y})'


@dataclass
class Carro(object):
    origem:     Deposito
    velocidade: int
    capacidade: float
    carga:      float = 0.0
    agenda:     Union[List[Cliente], List[Deposito]] = field(default_factory=list)
    fim:        int = 0
    _inicio = None

    def __post_init__(self):
        self.agenda = [self.origem]
        self.carga = self.capacidade
        self.fim = 0

    def __repr__(self): return f'Carro({self.origem}>>{len(self.agenda)}>>{self.agenda[-1]} [{self.carga}/{self.capacidade}] ({self.inicio}, {self.fim}, {self.velocidade}))'

    @property
    def posicao(self): return self.agenda[-1]

    @property
    def inicio(self):
        if len(self.agenda) == 0:
            return 0
        else:
            if self._inicio is None:
                primeiro_destino = self.agenda[1]
                self._inicio = max([0, primeiro_destino.inicio - self.tempo_deslocamento(primeiro_destino)])
            return self._inicio

    @property
    def clientes_atendidos(self):
        return set([str(cli) for cli in self.agenda if cli.tipo == 'Cliente'])

    def tempo_deslocamento(self, destino:Union[Cliente, Deposito], distancia=None) -> int:
        distancia = self.agenda[-1].distancia(destino) if distancia is None else distancia  # Speedup com pre-computado
        return int(distancia / self.velocidade) + 1

    def reabastecimento(self, deposito: Deposito):
        self.agenda.append(deposito)
        self.carga = self.capacidade

    def atendimento(self, cliente: Cliente):
        distancia = self.posicao.distancia(cliente)
        tempo_deslocamento = int(distancia / self.velocidade) + 1
        self.fim = max([self.fim + tempo_deslocamento + cliente.servico, cliente.inicio + cliente.servico])
        self.agenda.append(cliente)
        self.carga = self.carga - cliente.demanda

    def display(self):
        print(self)
        fim_anterior = 0
        cli_anterior = self.agenda[0]
        print('\t', cli_anterior)
        for cli in self.agenda[1:]:
            dist = cli_anterior.distancia(cli)
            tempo = int(dist/self.velocidade) + 1
            layover = 0 if ((fim_anterior + tempo) >= cli.inicio) else (cli.inicio - fim_anterior - tempo)
            layover += cli.servico
            print('\t\t', dist, '~', fim_anterior, '>>', tempo, '+', layover, '>>', fim_anterior+tempo+layover)
            print('\t', cli)
            fim_anterior = fim_anterior + tempo + layover
            cli_anterior = cli


def copia_carro(original: Carro):
    carro = Carro(origem=original.origem, velocidade=original.velocidade, capacidade=original.capacidade)
    for item in carro.agenda[1:]:
        if item.tipo == 'Cliente':
            carro.atendimento(item)
        else:
            carro.reabastecimento(item)
    return carro


@dataclass(frozen=True)
class Parametros(object):
    peso_distancia: float
    peso_urgencia: float
    peso_recursoes: float
    limite_recursoes: int
    clientes_recursao: int
    limite_iteracoes: int = 1000


# ######################################################################################################################
# UTILS


def le_mapa(arquivo):

    clientes = []
    with open(arquivo, 'r') as fin:
        for num_linha, linha in enumerate(fin):
            linha = linha.strip()
            if len(linha) == 0: continue
            if num_linha == 0:
                nome_teste = linha
                continue
            if num_linha == 4:
                max_carros, capacidade_carro = [int(v) for v in linha.split(' ') if len(v) > 0]
                continue
            if num_linha >= 9:
                _, x, y, demanda, inicio, fim, servico = [int(v) for v in linha.split(' ') if len(v) > 0]
                if num_linha == 9:
                    deposito = Deposito(x=x, y=y)
                else:
                    clientes.append(Cliente(x=x, y=y, demanda=demanda, inicio=inicio, fim=fim, servico=servico))
    return nome_teste, max_carros, capacidade_carro, deposito, clientes
