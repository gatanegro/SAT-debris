import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import pandas as pd
from scipy.integrate import odeint

# Constants
LZ = 1.23498288  # LZ scaling constant from COM theory
G = 6.67430e-11  # Gravitational constant (m^3 kg^-1 s^-2)
M_EARTH = 5.972e24  # Earth mass (kg)
M_MOON = 7.342e22  # Moon mass (kg)
R_EARTH = 6371  # Earth radius (km)
R_MOON = 1737.4  # Moon radius (km)
MOON_ORBIT = 384400  # Moon orbital radius (km)

def com_lz_attractor_radius(n):
    """
    Calculate stable orbital radii based on COM-LZ theory.
    
    Args:
        n: Harmonic step number (integer)
        
    Returns:
        Radius in kilometers
    """
    # Base radius calculation using LZ scaling
    base_radius = R_EARTH * (LZ ** n)
    
    # Apply octave reduction for resonance nodes
    octave_factor = ((n - 1) % 9 + 1) / 9
    
    # Final radius with harmonic adjustment
    radius = base_radius * (1 + 0.1 * np.sin(octave_factor * 2 * np.pi))
    
    return radius

def resonance_potential(r, n_vals):
    """
    Calculate the resonance potential at radius r based on COM-LZ attractors.
    
    Args:
        r: Radius to evaluate (km)
        n_vals: Array of harmonic steps to include
        
    Returns:
        Potential value (arbitrary units)
    """
    # Calculate attractor radii
    attractor_radii = np.array([com_lz_attractor_radius(n) for n in n_vals])
    
    # Calculate potential (inverse of distance to nearest attractor)
    potential = np.sum([1 / (1 + 0.01 * abs(r - r_a)**2) for r_a in attractor_radii])
    
    return potential

def drift_acceleration(r, t, n_vals):
    """
    Calculate acceleration due to resonance drift.
    
    Args:
        r: Current radius (km)
        t: Time (not used, required for odeint)
        n_vals: Harmonic steps to include
        
    Returns:
        Radial acceleration
    """
    # Calculate potential gradient (negative for attractive force)
    dr = 1.0  # Small step for numerical gradient
    pot_plus = resonance_potential(r + dr, n_vals)
    pot_minus = resonance_potential(r - dr, n_vals)
    gradient = (pot_plus - pot_minus) / (2 * dr)
    
    # Add damping term for stability
    damping = -0.1 * r[1]  # Proportional to velocity
    
    # Return acceleration (second derivative of position)
    return [r[1], -gradient + damping]

def plot_attractor_map(n_range, figsize=(12, 10)):
    """
    Generate an orbital attractor map based on COM-LZ theory.
    
    Args:
        n_range: Range of harmonic steps to plot
        figsize: Figure size tuple
        
    Returns:
        Figure and axes objects
    """
    # Calculate attractor radii
    n_vals = np.array(n_range)
    radii = np.array([com_lz_attractor_radius(n) for n in n_vals])
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot Earth
    earth = Circle((0, 0), R_EARTH, color='blue', alpha=0.7, label='Earth')
    ax.add_patch(earth)
    
    # Plot Moon orbit
    moon_orbit = Circle((0, 0), MOON_ORBIT, fill=False, color='gray', linestyle='--')
    ax.add_patch(moon_orbit)
    
    # Plot Moon
    moon_x = MOON_ORBIT * np.cos(np.pi/4)
    moon_y = MOON_ORBIT * np.sin(np.pi/4)
    moon = Circle((moon_x, moon_y), R_MOON, color='gray', alpha=0.7, label='Moon')
    ax.add_patch(moon)
    
    # Plot attractor rings
    for n, r in zip(n_vals, radii):
        circle = Circle((0, 0), r, fill=False, color='red', alpha=0.5)
        ax.add_patch(circle)
        ax.text(r*np.cos(np.pi/8), r*np.sin(np.pi/8), f'n={n}', fontsize=8)
    
    # Set axis limits and labels
    max_radius = max(radii) * 1.1
    ax.set_xlim(-max_radius, max_radius)
    ax.set_ylim(-max_radius, max_radius)
    ax.set_xlabel('Distance (km)')
    ax.set_ylabel('Distance (km)')
    ax.set_title('COM-LZ Orbital Attractor Map')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_aspect('equal')
    
    # Add legend
    ax.legend(loc='upper right')
    
    # Add scale information
    ax.text(0.02, 0.02, f'LZ = {LZ}', transform=ax.transAxes, fontsize=10)
    
    return fig, ax

def simulate_debris_drift(initial_radii, n_vals, t_span, num_points=1000):
    """
    Simulate the drift of debris particles under COM-LZ resonance.
    
    Args:
        initial_radii: List of initial radii for debris particles (km)
        n_vals: Harmonic steps to include in the potential
        t_span: Time span for simulation (arbitrary units)
        num_points: Number of time points to simulate
        
    Returns:
        DataFrame with simulation results
    """
    # Create time points
    t = np.linspace(0, t_span, num_points)
    
    # Initialize results storage
    results = []
    
    # Simulate each particle
    for i, r0 in enumerate(initial_radii):
        # Initial conditions [position, velocity]
        y0 = [r0, 0]
        
        # Solve ODE
        sol = odeint(drift_acceleration, y0, t, args=(n_vals,))
        
        # Store results
        for j in range(len(t)):
            results.append({
                'particle': i,
                'time': t[j],
                'radius': sol[j, 0],
                'velocity': sol[j, 1]
            })
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    return df

def plot_drift_simulation(df, n_vals, figsize=(12, 8)):
    """
    Plot the results of debris drift simulation.
    
    Args:
        df: DataFrame with simulation results
        n_vals: Harmonic steps included in the simulation
        figsize: Figure size tuple
        
    Returns:
        Figure and axes objects
    """
    # Calculate attractor radii
    attractor_radii = np.array([com_lz_attractor_radius(n) for n in n_vals])
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot each particle trajectory
    for particle in df['particle'].unique():
        particle_data = df[df['particle'] == particle]
        ax.plot(particle_data['time'], particle_data['radius'], 
                label=f'Debris {particle}')
    
    # Plot attractor radii
    for n, r in zip(n_vals, attractor_radii):
        ax.axhline(y=r, color='red', linestyle='--', alpha=0.5)
        ax.text(0, r, f'n={n}', fontsize=8, ha='left', va='bottom')
    
    # Set axis labels and title
    ax.set_xlabel('Time (arbitrary units)')
    ax.set_ylabel('Orbital Radius (km)')
    ax.set_title('Debris Drift Under COM-LZ Resonance')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # Add legend
    ax.legend(loc='upper right')
    
    return fig, ax

def plot_collector_field(n_target, figsize=(10, 10)):
    """
    Visualize the collector field at a target resonance band.
    
    Args:
        n_target: Target harmonic step for collector
        figsize: Figure size tuple
        
    Returns:
        Figure and axes objects
    """
    # Calculate target radius
    target_radius = com_lz_attractor_radius(n_target)
    
    # Create grid for field visualization
    x = np.linspace(-target_radius*1.5, target_radius*1.5, 100)
    y = np.linspace(-target_radius*1.5, target_radius*1.5, 100)
    X, Y = np.meshgrid(x, y)
    
    # Calculate radii at each point
    R = np.sqrt(X**2 + Y**2)
    
    # Calculate potential field
    n_vals = [n_target]
    Z = np.zeros_like(R)
    for i in range(Z.shape[0]):
        for j in range(Z.shape[1]):
            Z[i, j] = resonance_potential(R[i, j], n_vals)
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot potential field
    contour = ax.contourf(X, Y, Z, 20, cmap='viridis', alpha=0.7)
    fig.colorbar(contour, ax=ax, label='Resonance Potential')
    
    # Plot Earth
    earth = Circle((0, 0), R_EARTH, color='blue', alpha=0.7, label='Earth')
    ax.add_patch(earth)
    
    # Plot target radius
    target_circle = Circle((0, 0), target_radius, fill=False, color='red', 
                          linestyle='-', linewidth=2, label=f'Target n={n_target}')
    ax.add_patch(target_circle)
    
    # Plot collector satellite
    collector_angle = np.pi/4
    collector_x = target_radius * np.cos(collector_angle)
    collector_y = target_radius * np.sin(collector_angle)
    ax.scatter(collector_x, collector_y, color='white', s=100, 
               marker='*', label='Collector Satellite')
    
    # Add field lines
    ax.quiver(X[::5, ::5], Y[::5, ::5], 
              -np.gradient(Z, axis=1)[::5, ::5], 
              -np.gradient(Z, axis=0)[::5, ::5],
              color='white', alpha=0.5, scale=30)
    
    # Set axis limits and labels
    ax.set_xlim(-target_radius*1.5, target_radius*1.5)
    ax.set_ylim(-target_radius*1.5, target_radius*1.5)
    ax.set_xlabel('Distance (km)')
    ax.set_ylabel('Distance (km)')
    ax.set_title(f'Collector Field at COM-LZ Resonance Band n={n_target}')
    ax.grid(False)
    ax.set_aspect('equal')
    
    # Add legend
    ax.legend(loc='upper right')
    
    return fig, ax

def generate_all_visualizations():
    """
    Generate all visualizations for the paper and save them.
    
    Returns:
        Dictionary of figure paths
    """
    figure_paths = {}
    
    # 1. Attractor Map
    n_range = range(1, 11)
    fig, ax = plot_attractor_map(n_range)
    fig_path = '/home/ubuntu/attractor_map.png'
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figure_paths['attractor_map'] = fig_path
    
    # 2. Debris Drift Simulation
    n_vals = [3, 5, 7]
    initial_radii = [
        com_lz_attractor_radius(2) * 1.2,
        com_lz_attractor_radius(4) * 0.9,
        com_lz_attractor_radius(6) * 1.1,
        com_lz_attractor_radius(8) * 0.95
    ]
    df = simulate_debris_drift(initial_radii, n_vals, t_span=100)
    fig, ax = plot_drift_simulation(df, n_vals)
    fig_path = '/home/ubuntu/debris_drift.png'
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figure_paths['debris_drift'] = fig_path
    
    # 3. Collector Field
    fig, ax = plot_collector_field(n_target=5)
    fig_path = '/home/ubuntu/collector_field.png'
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figure_paths['collector_field'] = fig_path
    
    # 4. Verification of radii
    n_vals = np.arange(1, 11)
    radii = np.array([com_lz_attractor_radius(n) for n in n_vals])
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(n_vals, radii/1000, alpha=0.7)
    ax.set_xlabel('Harmonic Step (n)')
    ax.set_ylabel('Orbital Radius (thousand km)')
    ax.set_title('COM-LZ Predicted Stable Orbital Radii')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # Add text labels
    for n, r in zip(n_vals, radii):
        ax.text(n, r/1000 + 5, f'{r:.0f} km', ha='center')
    
    fig_path = '/home/ubuntu/radii_verification.png'
    fig.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    figure_paths['radii_verification'] = fig_path
    
    # Print radii for verification
    print("COM-LZ Predicted Stable Orbital Radii:")
    for n, r in zip(n_vals, radii):
        print(f"Step {n:2d} → Radius = {r:,.2f} km")
    
    return figure_paths

# Execute the code to generate all visualizations
if __name__ == "__main__":
    figure_paths = generate_all_visualizations()
    print("All visualizations generated and saved.")
    print(f"Figure paths: {figure_paths}")
