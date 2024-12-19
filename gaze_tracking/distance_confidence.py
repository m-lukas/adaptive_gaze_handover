import numpy as np

def calculate_confidence(distances, lambda_scale=1.0):
    """
    Calculate confidence scores based on the distances to fixation vectors.

    Parameters:
        distances (list or np.ndarray): List of distances to each fixation vector.
        lambda_scale (float): Scaling factor for sensitivity.

    Returns:
        np.ndarray: Array of confidence scores for each fixation vector.
    """
    distances = np.array(distances)
    # Compute the exponential weights
    probabilities = np.exp(-lambda_scale * distances**2)
    # Normalize to get confidence scores
    probabilities /= probabilities.sum()
    return probabilities

# Example Usage
if __name__ == "__main__":
    # Example distances to four fixation points
    distances = [0.6551600047266367, 0.42675855422445985, 0.1532715331425337, 0.513902447164921]
    lambda_scale = 10.0  # Sensitivity factor

    # Calculate confidence scores
    confidence_scores = calculate_confidence(distances, lambda_scale)

    print("Distances:", distances)
    print("Confidence Scores:", confidence_scores)
    print("Confidence Scores %:", [x*100 for x in confidence_scores])