import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import AutonomousFrontier from '@/pages/AutonomousFrontier';

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="xaxis" />,
  YAxis: () => <div data-testid="yaxis" />,
  Tooltip: () => <div data-testid="tooltip" />,
  CartesianGrid: () => <div data-testid="grid" />,
  Legend: () => <div data-testid="legend" />,
}));

describe('AutonomousFrontier Page', () => {
  it('renders the Autonomous Frontier header and default BioTwin-X tab', () => {
    render(<AutonomousFrontier />);

    expect(screen.getByText('Autonomous Frontier')).toBeDefined();
    expect(screen.getByText('Level 5 Health OS')).toBeDefined();
    expect(screen.getByText('Patient Baseline Controls')).toBeDefined();
    expect(screen.getByText('10-Year Multi-Organ Functional Trajectory')).toBeDefined();
  });

  it('switches to Causal do-Calculus tab and displays ITE and E-value', () => {
    render(<AutonomousFrontier />);

    const causalTabBtn = screen.getByText('Causal do-Calculus');
    fireEvent.click(causalTabBtn);

    expect(screen.getByText('Confounder Parameter Sliders')).toBeDefined();
    expect(screen.getByText('Pearl Level-3 Causal Counterfactual Deduction')).toBeDefined();
    expect(screen.getByText(/VanderWeele & Ding E-Value Sensitivity/i)).toBeDefined();
  });

  it('switches to Live Cybernetics & ICU tab and tests closed-loop titration step', () => {
    render(<AutonomousFrontier />);

    const cyberTabBtn = screen.getByText('Live Cybernetics & ICU');
    fireEvent.click(cyberTabBtn);

    expect(screen.getByText('Live Bedside Telemetry Monitor')).toBeDefined();
    expect(screen.getByText('Lyapunov-Constrained Actuator')).toBeDefined();

    const applyBtn = screen.getByText('Apply Closed-Loop Titration Step');
    fireEvent.click(applyBtn);

    expect(screen.getByText(/PROVEN STABLE/i)).toBeDefined();
  });

  it('switches to Generative Docking tab and calculates Delta G', () => {
    render(<AutonomousFrontier />);

    const dockingTabBtn = screen.getByText('Generative Docking');
    fireEvent.click(dockingTabBtn);

    expect(screen.getByText('Candidate Docking Setup')).toBeDefined();
    expect(screen.getByText(/Biophysical Binding Free Energy/i)).toBeDefined();

    const dockBtn = screen.getByText('Execute Molecular Docking');
    fireEvent.click(dockBtn);

    expect(screen.getByText(/-8.95 kcal\/mol/i)).toBeDefined();
  });

  it('switches to ZK Sovereign Passport tab and generates proof', () => {
    render(<AutonomousFrontier />);

    const zkTabBtn = screen.getByText('ZK Sovereign Passport');
    fireEvent.click(zkTabBtn);

    expect(screen.getByText('Patient Zero-Knowledge Wallet')).toBeDefined();
    expect(screen.getByText('Third-Party Verifier')).toBeDefined();

    const proveBtn = screen.getByText('Generate Non-Interactive ZK Proof');
    fireEvent.click(proveBtn);

    expect(screen.getByText(/Pedersen-Style Commitment C:/i)).toBeDefined();
    expect(screen.getByText(/Fiat-Shamir Proof Token/i)).toBeDefined();

    const verifyBtn = screen.getByText('Verify Assertion Without Private Data');
    fireEvent.click(verifyBtn);

    expect(screen.getByText(/CERTIFIED VALID/i)).toBeDefined();
  });
});
