import torch
import torch.nn as nn
import torch.optim as optim

# Automatically use GPU if available, otherwise fallback to CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Generator model: Generates synthetic durations based on noise and activity statistics
class Generator(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(Generator, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim + 2, 16),  # Input includes noise + activity mean + variance
            nn.ReLU(),
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, output_dim)  # Output: Generated duration
        )

    def forward(self, noise, activity_stats):
        """
        Forward pass: Combines noise with activity statistics to generate synthetic durations.
        """
        x = torch.cat((noise, activity_stats), dim=1)  # Concatenating noise and activity stats
        return self.model(x)

# Discriminator model: Distinguishes between real and synthetic durations
class Discriminator(nn.Module):
    def __init__(self, input_dim):
        super(Discriminator, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()  # Outputs probability of input being real (vs. synthetic)
        )

    def forward(self, data):
        """
        Forward pass: Predicts probability that the input is a real duration.
        """
        return self.model(data)

def train_gan(real_data, activity_data, t_threshold, epochs=500, batch_size=32):
    """
    Trains a GAN to generate synthetic durations that:
    - Maintain T-Closeness to the global activity distribution.
    - Preserve local similarity to the case-specific distribution.
    
    Args:
    real_data (list): Actual durations of an equivalence class (node).
    activity_data (list): Global distribution of activity durations.
    t_threshold (float): Maximum allowed difference from global distribution (T-Closeness).
    epochs (int): Number of training iterations.
    batch_size (int): Number of samples per training step.

    Returns:
    Generator: Trained model to generate synthetic durations.
    """
    input_dim = 1  # Single feature (duration)
    generator = Generator(input_dim, input_dim).to(device)
    discriminator = Discriminator(input_dim).to(device)
    
    # Binary Cross-Entropy loss function for discriminator and generator
    criterion = nn.BCELoss()
    optimizer_G = optim.Adam(generator.parameters(), lr=0.001)
    optimizer_D = optim.Adam(discriminator.parameters(), lr=0.001)
    
    # Convert real durations to PyTorch tensors and move to device
    real_data = torch.tensor(real_data, dtype=torch.float32).view(-1, 1).to(device)
    activity_data = torch.tensor(activity_data, dtype=torch.float32).view(-1, 1).to(device)

    # Compute mean and variance for activity distribution (global reference)
    activity_mean = activity_data.mean().item()
    activity_var = activity_data.var().item() if len(activity_data) > 1 else 0.0

    # Prepare repeated activity stats tensor for batch training
    activity_stats = torch.tensor([activity_mean, activity_var], dtype=torch.float32).repeat(batch_size, 1).to(device)

    for epoch in range(epochs):
        print(f" Now training epoch: {epoch}")
        for _ in range(len(real_data) // batch_size):
            # Select a random batch of real durations
            real_samples = real_data[torch.randint(0, len(real_data), (batch_size,))]

            # Generate synthetic durations using random noise
            noise = torch.randn(batch_size, input_dim).to(device)
            fake_samples = generator(noise, activity_stats)

            # Labels: 1 for real data, 0 for fake data
            real_labels = torch.ones(batch_size, 1).to(device)
            fake_labels = torch.zeros(batch_size, 1).to(device)

            # Train Discriminator: Predicts whether data is real or fake
            optimizer_D.zero_grad()
            loss_real = criterion(discriminator(real_samples), real_labels)  # Should predict close to 1
            loss_fake = criterion(discriminator(fake_samples.detach()), fake_labels)  # Should predict close to 0
            loss_D = (loss_real + loss_fake) / 2  # Average loss
            loss_D.backward()
            optimizer_D.step()

            # Train Generator: Should produce realistic durations
            optimizer_G.zero_grad()
            loss_G = criterion(discriminator(fake_samples), real_labels)  # Fool discriminator into thinking fake is real

            # **T-Closeness Constraint: Ensure synthetic values remain within threshold of global mean**
            distance_to_global = torch.abs(fake_samples.mean() - activity_mean)
            t_penalty = torch.relu(distance_to_global - t_threshold)  # Apply penalty if over threshold

            # **Local Similarity Constraint: Ensure synthetic values don't diverge too much from local distribution**
            distance_to_activity = torch.abs(fake_samples.mean() - real_data.mean())
            similarity_penalty = torch.relu(distance_to_activity - t_threshold / 2)  # Allows small deviation

            # Adjust Generator loss to incorporate T-Closeness & Local Similarity penalties
            loss_G += t_penalty + similarity_penalty
            loss_G.backward()
            optimizer_G.step()
        
    return generator  # Return trained model for future use

def generate_synthetic_durations(generator, activity_stats, num_samples=10):
    """
    Generates synthetic durations using the trained GAN.
    
    Args:
    generator (Generator): Trained model.
    activity_stats (list): Mean and variance of the global activity distribution.
    num_samples (int): Number of synthetic durations to generate.

    Returns:
    list: Array of generated synthetic durations.
    """
    with torch.no_grad():  # No gradient tracking for inference
        noise = torch.randn(num_samples, 1).to(device)
        activity_stats_tensor = torch.tensor(activity_stats, dtype=torch.float32).repeat(num_samples, 1).to(device)
        synthetic_durations = generator(noise, activity_stats_tensor).cpu().numpy().flatten()
    return synthetic_durations