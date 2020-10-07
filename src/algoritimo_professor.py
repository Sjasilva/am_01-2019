# -*- coding: utf-8 -*-

import threading
import time
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

# algorithm parameters
K = 10  # number of partitions
m = 1.6  # fuzzification parameter
T = 150
e = 10e-10
p = 3  # number of views
n = 2000

# importing datasets
fac_dataset = pd.read_csv('../data_bases/mfeat_fac.csv', header=None)
fou_dataset = pd.read_csv('../data_bases/mfeat_fou.csv', header=None)
kar_dataset = pd.read_csv('../data_bases/mfeat_kar.csv', header=None)

# convert data frames to array
fac_view = fac_dataset.iloc[:, :].values
fou_view = fou_dataset.iloc[:, :].values
kar_view = kar_dataset.iloc[:, :].values


def euclidean_distance(a, b):
    return np.linalg.norm(a - b)


def normalize_matrix(view):
    min_value = np.min(view)
    max_value = np.max(view)
    view = (view - min_value) / (max_value - min_value)
    return view


def dissimilarity_matrix(matrix, size):
    dis_matrix = np.zeros((size, size), dtype=float)
    for i in range(0, size):
        for j in range(0, size):
            dis_matrix[i, j] = euclidean_distance(a=matrix[i, :], b=matrix[j, :])
    return dis_matrix


def dist_object(i, k, pesos, dis_matrix, G):
    acc = 0
    for j in range(0, p):
        acc += pesos[k][j] * dis_matrix[j][i][G[k][j]]
    return acc


def objective_function(U, pesos, G, dis_matrix):
    objective = 0
    for k in range(0, K):
        for i in range(0, n):
            objective += np.power(U[i][k], m) * dist_object(i, k, pesos, dis_matrix, G)
    return objective


def compute_u(U, pesos, G, dis_matrix):
    for i in range(0, n):
        for k in range(0, K):
            membership = 0
            numerador = dist_object(i, k, pesos, dis_matrix, G)
            for h in range(0, K):
                membership += np.power(numerador / dist_object(i, h, pesos, dis_matrix, G), (1 / (m - 1)))
            membership = np.power(membership, -1)
            U[i][k] = membership
    return U


def crisp_partition(U):
    y = np.zeros(n, dtype=int)
    for i in range(0, n):
        y[i] = np.argmax(U[i])
    return y


def compute_weigths(U, pesos, G, dis_matrix):
    for j in range(0, p):
        for k in range(0, K):
            numerador = 1
            for h in range(0, p):
                soma = 0
                for i in range(0, n):
                    soma += np.power(U[i][k], m) * dis_matrix[h][i][G[k][h]]
                numerador = numerador * soma
            numerador = np.power(numerador, (1 / p))
            denominador = 0
            for i in range(0, n):
                denominador += np.power(U[i][k], m) * dis_matrix[j][i][G[k][j]]
            pesos[k][j] = numerador / denominador
    return pesos


def compute_G(G, U, dis_matrix):
    for k in range(0, K):
        for j in range(0, p):
            dist_vector = np.zeros(n, dtype=float)
            for h in range(0, n):
                soma = 0
                for i in range(0, n):
                    soma += np.power(U[i][k], m) * dis_matrix[j][i][h]
                dist_vector[h] = soma
            G[k][j] = np.argmin(dist_vector)
    return G


# Normalize matrixes (feature scaling)
fac_norm = normalize_matrix(fac_view)
fou_norm = normalize_matrix(fou_view)
kar_norm = normalize_matrix(kar_view)

# compute dissimilarity matrixes
fac_dis = dissimilarity_matrix(matrix=fac_norm, size=n)
fou_dis = dissimilarity_matrix(matrix=fou_norm, size=n)
kar_dis = dissimilarity_matrix(matrix=kar_norm, size=n)
dis_matrix = [fac_dis, fou_dis, kar_dis]


class MyThread(threading.Thread):

    def run(self):
        print('Começou {} tempo: {}'.format(self.getName(), datetime.now()))
        # Partição à priori em 10 classes
        y_priori = np.zeros(n, dtype=int)
        y_priori[200:400] = 1
        y_priori[400:600] = 2
        y_priori[600:800] = 3
        y_priori[800:1000] = 4
        y_priori[1000:1200] = 5
        y_priori[1200:1400] = 6
        y_priori[1400:1600] = 7
        y_priori[1600:1800] = 8
        y_priori[1800:2000] = 9

        # Inicialização dos vetores
        pesos = np.ones((K, p), dtype=float)
        U = np.zeros((n, K), dtype=float)
        G = np.random.choice(n, size=(K, p), replace=False)
        U = compute_u(U, pesos, G, dis_matrix)
        J = objective_function(U, pesos, G, dis_matrix)
        last_J = J + 100  # somado 100 apenas para entrar a primeira vez no laço.

        t = 0
        while (abs(J - last_J) >= e) and (t < T):
            last_J = J
            """Step 1"""
            G = compute_G(G, U, dis_matrix)
            """Step 2"""
            pesos = compute_weigths(U, pesos, G, dis_matrix)
            """Step 3"""
            U = compute_u(U, pesos, G, dis_matrix)
            J = objective_function(U, pesos, G, dis_matrix)
            t += 1

        # Partição crisp considerando o ultimo vetor U
        y = crisp_partition(U)
        # TODO: Imprimir os elementos da partição crisp (y) por grupo (classe), assim como a quantidade de elementos
        # exemplo: Grupo 1 -> elementos: 1,2,3,4,10,20 -> quantidade: 6
        rand_score = adjusted_rand_score(y_priori, y)

        with open('{}-output.txt'.format(self.getName()), 'w') as f:
            f.write('J = {}\n'.format(J))
            f.write('Rand = {}\n\n'.format(rand_score))

            f.write('Protótipos\n')
            for line in G:
                f.write(np.array_str(line) + "\n")
            f.write('\n')

            f.write('Pesos\n')
            for line in pesos:
                f.write(np.array_str(line) + "\n")
            f.write('\n')

        np.savetxt(fname='{}-crisp-partition.txt'.format(self.getName()), X=y, fmt='%d', delimiter=',',
                   header='Para carregar em um array, usar numpy.loadtxt()', comments='#')
        print('Finalizou {} tempo: {}'.format(self.getName(), datetime.now()))


def main():
    threads = []
    for x in range(60, 100):
        t = MyThread(name="Execução-{}".format(x + 1))
        threads.append(t)
        t.start()
        time.sleep(2)
    for x in threads:
        x.join()
    print("Acabou")


if __name__ == '__main__':
    main()
