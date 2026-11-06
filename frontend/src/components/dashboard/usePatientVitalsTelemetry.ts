import { useState, useEffect } from "react";
import { useAuthStore } from "@/lib/auth";
import { submitVitals, getDoctorPatientMonitoringSignals } from "@/lib/api";
import { getWebSocketUrl } from "@/lib/apiCore";
import { toast } from "@/lib/toast";
import type { ClinicalBed } from "@/components/dashboard/mockBeds";

interface UsePatientVitalsTelemetryProps {
  selectedPatientDbId: number | null;
  selectedBed: ClinicalBed | null;
  setSelectedBed: React.Dispatch<React.SetStateAction<ClinicalBed | null>>;
  setBeds: React.Dispatch<React.SetStateAction<ClinicalBed[]>>;
  activeTab: string;
}

export function usePatientVitalsTelemetry({
  selectedPatientDbId,
  selectedBed,
  setSelectedBed,
  setBeds,
  activeTab,
}: UsePatientVitalsTelemetryProps) {
  const [vitalsHr, setVitalsHr] = useState("");
  const [vitalsSpo2, setVitalsSpo2] = useState("");
  const [vitalsSystolic, setVitalsSystolic] = useState("");
  const [vitalsDiastolic, setVitalsDiastolic] = useState("");
  const [vitalsRr, setVitalsRr] = useState("");
  const [vitalsTemp, setVitalsTemp] = useState("");
  const [vitalsGlucose, setVitalsGlucose] = useState("");
  const [isSubmittingVitals, setIsSubmittingVitals] = useState(false);

  const [activeSignals, setActiveSignals] = useState<any[]>([]);
  const [signalsLoading, setSignalsLoading] = useState(false);

  const fetchSignalsForSelectedPatient = async (patientId: number) => {
    setSignalsLoading(true);
    try {
      const data = await getDoctorPatientMonitoringSignals(patientId);
      setActiveSignals((data as any).signals || data.open_signals || []);
    } catch {
      setActiveSignals([]);
    } finally {
      setSignalsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedPatientDbId && (activeTab === "vitals" || activeTab === "insights")) {
      fetchSignalsForSelectedPatient(selectedPatientDbId);
    }
  }, [selectedPatientDbId, activeTab]);

  const handleVitalsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPatientDbId) {
      toast.error("Could not associate patient record.");
      return;
    }

    setIsSubmittingVitals(true);
    try {
      await submitVitals({
        patient_id: selectedPatientDbId,
        source: "MANUAL_BEDSIDE",
        heart_rate: vitalsHr ? Number(vitalsHr) : undefined,
        spo2: vitalsSpo2 ? Number(vitalsSpo2) : undefined,
        systolic_bp: vitalsSystolic ? Number(vitalsSystolic) : undefined,
        diastolic_bp: vitalsDiastolic ? Number(vitalsDiastolic) : undefined,
        respiratory_rate: vitalsRr ? Number(vitalsRr) : undefined,
        temperature_c: vitalsTemp ? Number(vitalsTemp) : undefined,
      });

      toast.success("Vitals observation committed to EHR database.");

      if (vitalsHr || vitalsSpo2 || vitalsSystolic || vitalsDiastolic) {
        setBeds((prevBeds) =>
          prevBeds.map((bed) => {
            if (bed.name.toLowerCase().includes(selectedBed?.name?.toLowerCase() || "")) {
              return {
                ...bed,
                hr: vitalsHr ? Number(vitalsHr) : bed.hr,
                spo2: vitalsSpo2 ? Number(vitalsSpo2) : bed.spo2,
                bp:
                  vitalsSystolic && vitalsDiastolic
                    ? `${vitalsSystolic}/${vitalsDiastolic}`
                    : bed.bp,
                rr: vitalsRr ? Number(vitalsRr) : bed.rr,
              };
            }
            return bed;
          })
        );
      }

      setVitalsHr("");
      setVitalsSpo2("");
      setVitalsSystolic("");
      setVitalsDiastolic("");
      setVitalsRr("");
      setVitalsTemp("");
      setVitalsGlucose("");

      fetchSignalsForSelectedPatient(selectedPatientDbId);
    } catch (err: any) {
      toast.error(err.message || "Failed to record vitals.");
    } finally {
      setIsSubmittingVitals(false);
    }
  };

  useEffect(() => {
    if (!selectedPatientDbId) return;

    const token = useAuthStore.getState().token;
    const wsUrl =
      getWebSocketUrl(`/v1/telemetry/vitals/${selectedPatientDbId}`) +
      (token ? `?token=${token}` : "");
    let ws: WebSocket | null = null;
    let throttleTimeout: ReturnType<typeof setTimeout> | null = null;
    let lastUpdate = 0;
    let pendingData: any = null;

    try {
      ws = new WebSocket(wsUrl);
    } catch (err) {
      console.warn("Patient vitals WebSocket could not be initialized:", err);
      return;
    }

    const applyUpdates = () => {
      if (!pendingData) return;
      const data = pendingData;
      pendingData = null;
      lastUpdate = Date.now();

      const hr = data.heart_rate || 72;
      const spo2 = data.spo2 || 98;
      const bp = `${data.systolic_bp || 120}/${data.diastolic_bp || 80}`;
      const rr = data.respiratory_rate || 16;

      setSelectedBed((current) => {
        if (!current) return current;
        return {
          ...current,
          hr,
          spo2,
          rr,
          bp,
        };
      });

      setBeds((prevBeds) =>
        prevBeds.map((bed) => {
          const matchesSelected = bed.name
            .toLowerCase()
            .includes(selectedBed?.name?.toLowerCase() || "___nonexistent___");
          if (matchesSelected) {
            return {
              ...bed,
              hr,
              spo2,
              rr,
              bp,
            };
          }
          return bed;
        })
      );
    };

    ws.onmessage = (event) => {
      try {
        pendingData = JSON.parse(event.data);
        const timeSinceLast = Date.now() - lastUpdate;
        if (timeSinceLast >= 500) {
          applyUpdates();
        } else if (!throttleTimeout) {
          throttleTimeout = setTimeout(() => {
            throttleTimeout = null;
            applyUpdates();
          }, 500 - timeSinceLast);
        }
      } catch (err) {
        console.warn("Failed to parse live vitals WebSocket message:", err);
      }
    };

    ws.onerror = (err) => {
      console.warn("Patient vitals WebSocket connection error:", err);
    };

    return () => {
      if (ws) {
        try {
          ws.close();
        } catch {}
      }
      if (throttleTimeout) clearTimeout(throttleTimeout);
    };
  }, [selectedPatientDbId, selectedBed?.name, setSelectedBed, setBeds]);

  return {
    vitalsHr,
    setVitalsHr,
    vitalsSpo2,
    setVitalsSpo2,
    vitalsSystolic,
    setVitalsSystolic,
    vitalsDiastolic,
    setVitalsDiastolic,
    vitalsRr,
    setVitalsRr,
    vitalsTemp,
    setVitalsTemp,
    vitalsGlucose,
    setVitalsGlucose,
    isSubmittingVitals,
    handleVitalsSubmit,
    activeSignals,
    signalsLoading,
  };
}
