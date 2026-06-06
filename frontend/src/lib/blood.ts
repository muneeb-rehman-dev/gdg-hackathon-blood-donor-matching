export const BLOOD_GROUPS = ["A+","A-","B+","B-","AB+","AB-","O+","O-"] as const;
export type BloodGroup = typeof BLOOD_GROUPS[number];

// Recipient -> compatible donor blood groups
export const COMPATIBLE: Record<BloodGroup, BloodGroup[]> = {
  "A+":  ["A+","A-","O+","O-"],
  "A-":  ["A-","O-"],
  "B+":  ["B+","B-","O+","O-"],
  "B-":  ["B-","O-"],
  "AB+": ["A+","A-","B+","B-","AB+","AB-","O+","O-"],
  "AB-": ["A-","B-","AB-","O-"],
  "O+":  ["O+","O-"],
  "O-":  ["O-"],
};

// Karachi area coordinates (centre of each area)
export const AREAS: Record<string, { lat: number; lng: number }> = {
  "Clifton":          { lat: 24.8100, lng: 67.0300 },
  "DHA":              { lat: 24.8100, lng: 67.0750 },
  "Gulshan-e-Iqbal":  { lat: 24.9350, lng: 67.1050 },
  "Nazimabad":        { lat: 24.9150, lng: 67.0350 },
  "North Karachi":    { lat: 24.9650, lng: 67.0650 },
  "Saddar":           { lat: 24.8700, lng: 67.0100 },
  "Korangi":          { lat: 24.8450, lng: 67.1150 },
  "Malir":            { lat: 24.8900, lng: 67.1950 },
  "Lyari":            { lat: 24.8750, lng: 66.9950 },
};

export function haversineKm(a: {lat:number;lng:number}, b: {lat:number;lng:number}) {
  const R = 6371;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const s = Math.sin(dLat/2)**2 + Math.cos(toRad(a.lat))*Math.cos(toRad(b.lat))*Math.sin(dLng/2)**2;
  return 2 * R * Math.asin(Math.sqrt(s));
}
