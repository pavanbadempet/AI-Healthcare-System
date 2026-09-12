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

  it('switches to Delphi Consensus Swarm tab and executes deliberation', () => {
    render(<AutonomousFrontier />);

    const delphiTabBtn = screen.getByText('Delphi Consensus Swarm');
    fireEvent.click(delphiTabBtn);

    expect(screen.getByText('Delphi Swarm with Adversarial Falsification')).toBeDefined();
    expect(screen.getByText('Internist')).toBeDefined();
    expect(screen.getByText('Pharmacologist')).toBeDefined();
    expect(screen.getByText('Intensivist')).toBeDefined();
    expect(screen.getByText("Adversarial Skeptic")).toBeDefined();

    const delibBtn = screen.getByText('Execute Delphi Rounds');
    fireEvent.click(delibBtn);

    expect(screen.getByText(/Delphi Consensus & Falsification Summary/i)).toBeDefined();
  });

  it('switches to Neuro-Symbolic PGx tab and runs axiomatic proof', () => {
    render(<AutonomousFrontier />);

    const neuroTabBtn = screen.getByText('Neuro-Symbolic PGx');
    fireEvent.click(neuroTabBtn);

    expect(screen.getByText('First-Order Logic (FOL) CPIC Pharmacogenomics Prover')).toBeDefined();
    expect(screen.getByText('Patient Premises & Axioms')).toBeDefined();

    const proveBtn = screen.getByText('Prove Regimen Safety (FOL)');
    fireEvent.click(proveBtn);

    expect(screen.getByText(/First-Order Logic Resolution Result/i)).toBeDefined();
  });

  it('switches to Offline CRDT Sync tab and triggers join-semilattice merge', () => {
    render(<AutonomousFrontier />);

    const crdtTabBtn = screen.getByText('Offline CRDT Sync');
    fireEvent.click(crdtTabBtn);

    expect(screen.getByText('Offline-First Clinical CRDT Synchronization')).toBeDefined();
    expect(screen.getByText(/Ambulance Node A/i)).toBeDefined();
    expect(screen.getByText(/Trauma Bay Node B/i)).toBeDefined();

    const mergeBtn = screen.getByText(/Trigger Join-Semilattice Merge/i);
    fireEvent.click(mergeBtn);

    expect(screen.getByText(/Mathematically Converged Patient Chart State/i)).toBeDefined();
  });

  it('switches to Chaos & Concurrency tab and executes order idempotency check', () => {
    render(<AutonomousFrontier />);

    const chaosTabBtn = screen.getByText('Chaos & Concurrency');
    fireEvent.click(chaosTabBtn);

    expect(screen.getByText('Adaptive Concurrency, Idempotency & Chaos Mesh')).toBeDefined();
    expect(screen.getByText('Adaptive Concurrency Limiter')).toBeDefined();
    expect(screen.getByText('Cryptographic Idempotency Engine')).toBeDefined();
    expect(screen.getByText('Chaos Mesh Circuit Breaker')).toBeDefined();

    const orderBtn = screen.getByText('Submit High-Stakes Clinical Order');
    fireEvent.click(orderBtn);

    expect(screen.getByText(/SUCCESS \(HTTP 200\)/i)).toBeDefined();
  });
});
