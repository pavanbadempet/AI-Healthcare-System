export interface ClinicalBed {
  bed: string;
  name: string;
  status: "Stable" | "Alert";
  hr: number;
  spo2: number;
  bp: string;
  rr: number;
  ecgD: string;
}

export const INITIAL_BEDS: ClinicalBed[] = [
  {
    bed: "ICU-A-01",
    name: "Marcus Thorne",
    status: "Alert",
    hr: 112,
    spo2: 91,
    bp: "148/94",
    rr: 24,
    ecgD: "M0,50 L35,50 L40,15 L50,85 L60,50 L95,50 L100,15 L110,85 L120,50 L155,50 L160,15 L170,85 L180,50 L215,50 L220,15 L230,85 L240,50 L275,50 L280,15 L290,85 L300,50 L335,50 L340,15 L350,85 L360,50 L400,50",
  },
  {
    bed: "ICU-A-03",
    name: "Sarah Jenkins",
    status: "Stable",
    hr: 72,
    spo2: 98,
    bp: "118/76",
    rr: 16,
    ecgD: "M0,50 L45,50 L55,20 L65,80 L75,50 L120,50 L130,20 L140,80 L150,50 L195,50 L205,20 L215,80 L225,50 L270,50 L280,20 L290,80 L300,50 L345,50 L355,20 L365,80 L375,50 L400,50",
  },
  {
    bed: "ICU-A-05",
    name: "Linda Zhao",
    status: "Stable",
    hr: 68,
    spo2: 99,
    bp: "112/72",
    rr: 14,
    ecgD: "M0,50 L50,50 L60,25 L70,75 L80,50 L130,50 L140,25 L150,75 L160,50 L210,50 L220,25 L230,75 L240,50 L290,50 L300,25 L310,75 L320,50 L370,50 L380,25 L390,75 L400,50",
  },
  {
    bed: "ICU-A-07",
    name: "Robert G.",
    status: "Stable",
    hr: 82,
    spo2: 95,
    bp: "135/88",
    rr: 18,
    ecgD: "M0,50 L40,50 L50,18 L60,82 L70,50 L110,50 L120,18 L130,82 L140,50 L180,50 L190,18 L200,82 L210,50 L250,50 L260,18 L270,82 L280,50 L320,50 L330,18 L340,82 L350,50 L400,50",
  },
  {
    bed: "ICU-A-09",
    name: "Emily Watson",
    status: "Stable",
    hr: 64,
    spo2: 97,
    bp: "116/74",
    rr: 15,
    ecgD: "M0,50 L55,50 L65,22 L75,78 L85,50 L140,50 L150,22 L160,78 L170,50 L225,50 L235,22 L245,78 L255,50 L310,50 L320,22 L330,78 L340,50 L395,50 L400,50",
  },
  {
    bed: "ICU-A-11",
    name: "Oscar Meyer",
    status: "Stable",
    hr: 76,
    spo2: 96,
    bp: "128/82",
    rr: 17,
    ecgD: "M0,50 L45,50 L55,20 L65,80 L75,50 L120,50 L130,20 L140,80 L150,50 L195,50 L205,20 L215,80 L225,50 L270,50 L280,20 L290,80 L300,50 L345,50 L355,20 L365,80 L375,50 L400,50",
  },
];
