import numpy as np

# Create two 3x1 numpy.ndarray vectors
vector1 = np.array([[1], [2], [3]])
vector2 = np.array([[4], [5], [6]])

# Add both vectors to a list
vectors_list = [vector1, vector2]

# Compute the mean vector
mean_vector = np.mean(vectors_list, axis=0)

print("Vector 1:")
print(vector1)
print("\nVector 2:")
print(vector2)
print("\nMean Vector:")
print(mean_vector)
