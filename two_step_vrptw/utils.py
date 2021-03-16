#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""objetos.py: Objetos e utilidades necessários para a implementação do algoritmo"""

__copyright__ = "Copyright (c) 2021 Isabella Freitas & José Fonseca. MIT. See attached LICENSE.txt file"


from math import sqrt
from sys import maxsize as int_inf
from typing import List, Tuple, Union, Dict
from dataclasses import dataclass, field
from functools import lru_cache as memoized

from pandas import DataFrame
from numpy import power, sqrt


# ######################################################################################################################
# DATA CLASSES BÁSICAS


@dataclass(frozen=True)
class Parametros(object):
    peso_distancia: float
    peso_urgencia: float
    peso_recursoes: float
    limite_recursoes: int
    clientes_recursao: int
    limite_iteracoes: int = 1000


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


@dataclass(frozen=True, init=False)
class Mapa(object):
    arquivo: str
    nome: str
    max_carros: int
    capacidade_carro: float
    deposito: Deposito
    clientes: List[Cliente]
    matriz_de_distancias: DataFrame
    dict_referencias: Dict

    def __init__(self, arquivo: str):
        object.__setattr__(self, 'arquivo', arquivo)
        nome, max_carros, capacidade_carro, deposito, clientes = self.parse_arquivo(arquivo)
        matriz_de_distancias, dict_referencias = self.cria_matriz_de_distancias(deposito, clientes)
        object.__setattr__(self, 'nome', nome)
        object.__setattr__(self, 'max_carros', max_carros)
        object.__setattr__(self, 'capacidade_carro', capacidade_carro)
        object.__setattr__(self, 'deposito', deposito)
        object.__setattr__(self, 'clientes', clientes)
        object.__setattr__(self, 'matriz_de_distancias', matriz_de_distancias)
        object.__setattr__(self, 'dict_referencias', dict_referencias)

    def __repr__(self): return f'MAPA({self.nome}: {self.max_carros}x{self.capacidade_carro} ${len(self.clientes)})'
    def __str__(self): return self.__repr__()

    @staticmethod
    def parse_arquivo(arquivo):
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

    @staticmethod
    def cria_matriz_de_distancias(deposito: Deposito, clientes: List[Cliente]) -> (DataFrame, dict):
        lista_referencia = [deposito] + clientes
        str_lista_referencia = list(map(str, lista_referencia))

        # Calculamos as distancias entre cada ponto no mapa
        df_x = DataFrame([[i.x for i in lista_referencia]] * len(lista_referencia),
                         columns=str_lista_referencia, index=str_lista_referencia)
        df_x = (df_x - df_x.T).applymap(lambda x: power(x, 2))
        df_y = DataFrame([[i.y for i in lista_referencia]] * len(lista_referencia),
                         columns=str_lista_referencia, index=str_lista_referencia)
        df_y = (df_y - df_y.T).applymap(lambda y: power(y, 2))
        df_distancias = (df_x + df_y).applymap(sqrt).astype(float).round(3)

        return df_distancias, dict(zip(str_lista_referencia, lista_referencia))


# ######################################################################################################################
# DATA CLASSES DE AGENTES


@dataclass
class Carro(object):
    id:         str
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

    def __repr__(self): return f'Carro{self.id}(O+{len(self.agenda)}>>{self.posicao} |{self.carga}| [{self.inicio}, {self.fim}])'
    def __str__(self): return self.__repr__()

    @property
    def posicao(self): return self.agenda[-1]

    @property
    def inicio(self):
        return 0 if len(self.agenda) == 0 else max([
            0, self.agenda[1].inicio - self.tempo_deslocamento(origem=self.agenda[0], destino=self.agenda[1])])

    @property
    def clientes_atendidos(self) -> set:
        return set([str(cli) for cli in self.agenda if cli.tipo == 'Cliente'])

    def tempo_deslocamento(self, destino:Union[Cliente, Deposito], distancia=None, origem=None) -> int:
        pos = self.posicao if origem is None else origem
        distancia = pos.distancia(destino) if distancia is None else distancia  # Speedup com pre-computado
        return int(distancia / self.velocidade) + 1

    def reabastecimento(self, deposito: Deposito):
        self.agenda.append(deposito)
        self.carga = self.capacidade

    def atendimento(self, cliente: Cliente):
        distancia = self.posicao.distancia(cliente)
        tempo_deslocamento = self.tempo_deslocamento(cliente, distancia=distancia)
        self.fim = max([self.fim + tempo_deslocamento + cliente.servico, cliente.inicio + cliente.servico])
        self.agenda.append(cliente)
        self.carga = self.carga - cliente.demanda
        return (distancia, tempo_deslocamento)

    def resultado(self, display=True) -> Tuple[int, float, int, int, int]:
        distancia_total = 0
        tempo_deslocamento_total = 0
        tempo_layover_total = 0
        fim_anterior = 0
        cli_anterior = self.agenda[0]
        if display: print(self)
        if display: print('\t', cli_anterior)

        for cli in self.agenda[1:]:
            distancia = cli_anterior.distancia(cli)
            tempo_deslocamento = int(distancia/self.velocidade) + 1
            tempo_layover = max([0, cli.inicio - (fim_anterior + tempo_deslocamento)]) + cli.servico
            if display: print('\t\t', distancia, '~', fim_anterior, '>>', tempo_deslocamento, '+', tempo_layover, '>>', fim_anterior+tempo_deslocamento+tempo_layover)
            if display: print('\t', cli)
            fim_anterior = fim_anterior + tempo_deslocamento + tempo_layover
            cli_anterior = cli

            distancia_total += distancia
            tempo_deslocamento_total += tempo_deslocamento
            tempo_layover_total += tempo_layover
        return self.inicio, distancia_total, tempo_deslocamento_total, tempo_layover_total, self.fim


def copia_carro(original: Carro):
    carro = Carro(id='COPY:'+original.id, origem=original.origem, velocidade=original.velocidade, capacidade=original.capacidade)
    for item in carro.agenda[1:]:
        if item.tipo == 'Cliente':
            carro.atendimento(item)
        else:
            carro.reabastecimento(item)
    return carro


@dataclass(frozen=False, init=False)
class Frota(object):
    mapa: Mapa
    max_carros: int
    capacidade_carro: float
    velocidade_carro: int
    carros: Dict
    deposito: Deposito

    def __init__(self, mapa: Mapa, velocidade_carro: int):
        self.velocidade_carro = velocidade_carro
        self.mapa = mapa
        self.max_carros = mapa.max_carros
        self.capacidade_carro = mapa.capacidade_carro
        self.deposito = mapa.deposito
        self.carros = {}

    def __getitem__(self, item): return self.mapa.dict_referencias[item]
    def __repr__(self): return f'Frota<{self.mapa.nome}>(|{len(self.carros)}/{self.mapa.max_carros}| x {len(self.clientes_atendidos)}/{len(self.mapa.clientes)}])'
    def __str__(self): return self.__repr__()

    @property
    def clientes_atendidos(self) -> set:
        result = set()
        for carro in self.carros.values():
            result = result.union(carro.clientes_atendidos)
        return result

    @property
    def clientes_faltantes(self) -> set:
        return set(map(str, self.mapa.clientes)) - self.clientes_atendidos

    @property
    def sumario(self) -> DataFrame:
        sumario = []
        for carro in self.carros.values():
            inicio, distancia, t_desloc, t_layover, fim = carro.resultado(display=False)
            sumario.append({'carro': carro.id, 'inicio': inicio, 'fim': fim, 'distancia': distancia,
                            'tempo_deslocamento': t_desloc, 'tempo_layover': t_layover,
                            'qtd_clientes': len(carro.clientes_atendidos)})
        sumario = DataFrame(sumario)
        sumario.loc[:, 'tempo_total'] = sumario['fim'] - sumario['inicio']
        return sumario

    def novo_carro(self) -> Carro:
        carro = Carro(str(len(self.carros)), self.deposito, self.velocidade_carro, self.capacidade_carro)
        self.carros[carro.id] = carro
        return carro
