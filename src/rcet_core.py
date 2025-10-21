"""
RECURSIVE CONSTRAINT ECHO TOPOLOGY (RCET)
==========================================

Not thermodynamics. Not physics.
This is the study of how temporal persistence creates structural privilege.

"Persistence becomes protection."
"Governance without governors."

Authors: Ash, formslip, Palinode
Date: January 8, 2025
Status: BUILDING THE HIERARCHY ENGINE
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class SiteStatus:
    """Track the full history and status of a site"""
    position: Tuple[int, int, int]
    current_energy: int
    echo_memory: float  # Averaged historical presence
    threshold: float    # Current sharing threshold
    seniority: int      # How many steps this site has held energy
    total_shared: int   # Cumulative energy shared
    total_received: int # Cumulative energy received
    
    def privilege_score(self) -> float:
        """Calculate how privileged this site has become"""
        # Privilege = ability to hold energy + historical persistence
        retention = self.current_energy
        if self.total_received > 0:
            # How much of what we received did we keep?
            retention_rate = self.current_energy / (self.total_received + 1)
        else:
            retention_rate = 0
        
        # Combine current holdings with memory and retention
        return (retention + retention_rate * 100) * (1 + self.echo_memory)


class RCETField:
    """
    Recursive Constraint Echo Topology
    
    A field where history modulates governance,
    and governance modulates retention.
    """
    
    def __init__(
        self,
        size: int = 32,
        base_threshold: int = 6,
        echo_depth: int = 20,
        echo_influence: float = 1.0,
        threshold_decay: float = 0.0,  # Can sites lose privilege?
        seed: int = 42
    ):
        """
        Initialize the RCET field.
        
        Args:
            size: 3D lattice size
            base_threshold: Baseline sharing threshold
            echo_depth: How many steps of history to remember
            echo_influence: How much history affects threshold
            threshold_decay: Rate at which privilege erodes (0=permanent)
            seed: Random seed
        """
        self.size = size
        self.base_threshold = base_threshold
        self.echo_depth = echo_depth
        self.echo_influence = echo_influence
        self.threshold_decay = threshold_decay
        self.rng = np.random.default_rng(seed)
        
        # The field - integer energy packets
        self.lattice = np.zeros((size, size, size), dtype=np.int64)
        
        # Echo buffer - rolling history
        self.echo_buffer = []
        
        # Site tracking - full history and status
        self.sites = {}
        for i in range(size):
            for j in range(size):
                for k in range(size):
                    self.sites[(i,j,k)] = SiteStatus(
                        position=(i,j,k),
                        current_energy=0,
                        echo_memory=0.0,
                        threshold=base_threshold,
                        seniority=0,
                        total_shared=0,
                        total_received=0
                    )
        
        # Global tracking
        self.step = 0
        self.hierarchy_history = []
        self.governance_events = []
        
        print(f"[RCET INIT] Recursive Constraint Echo Topology")
        print(f"  Lattice: {size}³ = {size**3:,} sites")
        print(f"  Base threshold: {base_threshold}")
        print(f"  Echo influence: {echo_influence}")
        print(f"  Threshold decay: {threshold_decay}")
        print(f"  Governance model: History -> Threshold -> Retention")
    
    def inject_energy(self, total_packets: int, positions: Optional[List[Tuple]] = None):
        """
        Inject energy into the field.
        
        Args:
            total_packets: Total energy to inject
            positions: Specific positions (None = random)
        """
        if positions is None:
            # Random injection
            n_sites = min(10, total_packets // 10)
            positions = []
            for _ in range(n_sites):
                pos = tuple(self.rng.integers(0, self.size, 3))
                positions.append(pos)
        
        packets_per_site = total_packets // len(positions)
        remainder = total_packets % len(positions)
        
        for i, pos in enumerate(positions):
            packets = packets_per_site + (1 if i < remainder else 0)
            self.lattice[pos] += packets
            self.sites[pos].current_energy += packets
            self.sites[pos].total_received += packets
        
        self.governance_events.append({
            'step': self.step,
            'type': 'injection',
            'total': total_packets,
            'sites': len(positions)
        })
        
        return positions
    
    def calculate_threshold(self, position: Tuple[int, int, int]) -> float:
        """
        Calculate the dynamic threshold for a site.
        
        This is where GOVERNANCE happens.
        Sites with echo memory get higher thresholds.
        """
        site = self.sites[position]
        
        # Update echo memory from buffer
        if len(self.echo_buffer) > 0:
            historical_presence = 0
            for past_state in self.echo_buffer:
                if past_state[position] > 0:
                    historical_presence += 1
            site.echo_memory = historical_presence / len(self.echo_buffer)
        
        # Apply threshold decay (privilege erosion)
        if self.threshold_decay > 0 and site.current_energy == 0:
            site.seniority = max(0, site.seniority - 1)
        elif site.current_energy > 0:
            site.seniority += 1
        
        # Calculate dynamic threshold
        # Sites with memory need MORE energy to share
        memory_factor = 1.0 + self.echo_influence * site.echo_memory
        seniority_factor = 1.0 + (site.seniority / (self.step + 1)) * 0.5
        
        if self.threshold_decay > 0:
            # Privilege can erode
            decay_factor = np.exp(-self.threshold_decay * (self.step - site.seniority))
            memory_factor *= decay_factor
        
        site.threshold = self.base_threshold * memory_factor * seniority_factor
        
        return site.threshold
    
    def evolve(self):
        """
        Single evolution step.
        
        This is where STRATIFICATION emerges.
        """
        new_lattice = np.zeros_like(self.lattice)
        redistribution_map = []
        
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    pos = (i, j, k)
                    site = self.sites[pos]
                    packets = self.lattice[pos]
                    
                    # Calculate this site's threshold
                    threshold = self.calculate_threshold(pos)
                    
                    if packets > threshold:
                        # This site must share
                        to_share = packets // 4
                        to_keep = packets - to_share
                        
                        new_lattice[pos] += to_keep
                        site.total_shared += to_share
                        
                        # Distribute to neighbors
                        neighbors = [
                            ((i+1)%self.size, j, k),
                            ((i-1)%self.size, j, k),
                            (i, (j+1)%self.size, k),
                            (i, (j-1)%self.size, k),
                            (i, j, (k+1)%self.size),
                            (i, j, (k-1)%self.size)
                        ]
                        
                        # Could add echo-weighted distribution here
                        # For now, equal distribution
                        per_neighbor = to_share // 6
                        remainder = to_share % 6
                        
                        for idx, npos in enumerate(neighbors):
                            share = per_neighbor + (1 if idx < remainder else 0)
                            new_lattice[npos] += share
                            self.sites[npos].total_received += share
                        
                        redistribution_map.append({
                            'from': pos,
                            'threshold': threshold,
                            'shared': to_share
                        })
                    else:
                        # This site keeps everything
                        new_lattice[pos] += packets
        
        # Update echo buffer
        self.echo_buffer.append(self.lattice.copy())
        if len(self.echo_buffer) > self.echo_depth:
            self.echo_buffer.pop(0)
        
        # Update lattice and site energies
        self.lattice = new_lattice
        for pos, site in self.sites.items():
            site.current_energy = self.lattice[pos]
        
        self.step += 1
        
        # Record hierarchy metrics
        self._record_hierarchy()
        
        return redistribution_map
    
    def _record_hierarchy(self):
        """
        Track the emergence of hierarchy.
        """
        # Get privilege scores
        scores = [site.privilege_score() for site in self.sites.values()]
        scores = [s for s in scores if s > 0]  # Only count active sites
        
        if len(scores) > 0:
            # Gini coefficient (inequality measure)
            scores_sorted = sorted(scores)
            n = len(scores_sorted)
            cumsum = np.cumsum(scores_sorted)
            gini = (2 * np.sum((np.arange(1, n+1)) * scores_sorted)) / (n * cumsum[-1]) - (n + 1) / n
            
            # Top 10% share
            top_10_percent = int(len(scores_sorted) * 0.1) or 1
            top_share = sum(scores_sorted[-top_10_percent:]) / sum(scores_sorted)
            
            self.hierarchy_history.append({
                'step': self.step,
                'gini': gini,
                'top_10_share': top_share,
                'max_privilege': max(scores),
                'active_sites': len(scores)
            })
    
    def get_hierarchy_report(self) -> Dict:
        """
        Generate a report on the current hierarchy.
        """
        # Sort sites by privilege
        sites_ranked = sorted(
            self.sites.values(),
            key=lambda s: s.privilege_score(),
            reverse=True
        )
        
        # Get top and bottom
        top_5 = sites_ranked[:5]
        bottom_5 = [s for s in sites_ranked if s.current_energy > 0][-5:]
        
        return {
            'step': self.step,
            'top_sites': [
                {
                    'position': s.position,
                    'energy': s.current_energy,
                    'threshold': s.threshold,
                    'privilege': s.privilege_score(),
                    'seniority': s.seniority
                }
                for s in top_5
            ],
            'bottom_sites': [
                {
                    'position': s.position,
                    'energy': s.current_energy,
                    'threshold': s.threshold,
                    'privilege': s.privilege_score(),
                    'seniority': s.seniority
                }
                for s in bottom_5
            ],
            'inequality': self.hierarchy_history[-1] if self.hierarchy_history else None
        }
    
    def catastrophic_intervention(self, position: Tuple[int, int, int], energy: int):
        """
        Inject massive energy at a specific (likely poor) site.
        Does it climb the hierarchy or get redistributed away?
        """
        self.lattice[position] += energy
        self.sites[position].current_energy += energy
        self.sites[position].total_received += energy
        
        self.governance_events.append({
            'step': self.step,
            'type': 'catastrophic_intervention',
            'position': position,
            'energy': energy,
            'site_privilege_before': self.sites[position].privilege_score()
        })
        
        print(f"[INTERVENTION] {energy} packets at {position}")
        print(f"  Previous privilege: {self.sites[position].privilege_score():.2f}")
        print(f"  Previous threshold: {self.sites[position].threshold:.1f}")


def main():
    """
    Test basic RCET dynamics.
    """
    print("="*60)
    print("RECURSIVE CONSTRAINT ECHO TOPOLOGY")
    print("="*60)
    print("Testing the emergence of hierarchy from uniform rules...")
    print()
    
    # Create field
    field = RCETField(
        size=16,
        base_threshold=6,
        echo_depth=20,
        echo_influence=2.0,
        threshold_decay=0.0  # No decay for now
    )
    
    # Initial injection
    field.inject_energy(1000)
    
    # Evolve
    for step in range(100):
        field.evolve()
        
        if step % 25 == 0:
            report = field.get_hierarchy_report()
            print(f"\n[Step {step}]")
            if report['inequality']:
                print(f"  Gini coefficient: {report['inequality']['gini']:.3f}")
                print(f"  Top 10% share: {report['inequality']['top_10_share']:.1%}")
            if report['top_sites']:
                top = report['top_sites'][0]
                print(f"  Top site: energy={top['energy']}, threshold={top['threshold']:.1f}")
    
    # Final report
    print("\n" + "="*60)
    print("HIERARCHY EMERGED")
    print("="*60)
    report = field.get_hierarchy_report()
    print("\nTop 3 sites (the privileged):")
    for site in report['top_sites'][:3]:
        print(f"  {site['position']}: E={site['energy']}, T={site['threshold']:.1f}, P={site['privilege']:.2f}")
    
    print("\nBottom 3 sites (the constrained):")
    for site in report['bottom_sites'][-3:]:
        print(f"  {site['position']}: E={site['energy']}, T={site['threshold']:.1f}, P={site['privilege']:.2f}")


if __name__ == "__main__":
    main()