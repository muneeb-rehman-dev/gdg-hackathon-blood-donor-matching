
CREATE TYPE public.blood_group AS ENUM ('A+','A-','B+','B-','AB+','AB-','O+','O-');
CREATE TYPE public.response_status AS ENUM ('pending','accepted','declined');

CREATE TABLE public.donors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  blood_group public.blood_group NOT NULL,
  phone TEXT NOT NULL,
  city TEXT NOT NULL,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  available BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.donors TO anon, authenticated;
GRANT ALL ON public.donors TO service_role;
ALTER TABLE public.donors ENABLE ROW LEVEL SECURITY;
CREATE POLICY "donors public read" ON public.donors FOR SELECT USING (true);
CREATE POLICY "donors public update" ON public.donors FOR UPDATE USING (true) WITH CHECK (true);

CREATE TABLE public.blood_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  seeker_name TEXT NOT NULL,
  seeker_phone TEXT NOT NULL,
  bottles INT NOT NULL CHECK (bottles > 0),
  blood_group public.blood_group NOT NULL,
  hospital TEXT NOT NULL,
  city TEXT NOT NULL,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  needed_at TIMESTAMPTZ NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.blood_requests TO anon, authenticated;
GRANT ALL ON public.blood_requests TO service_role;
ALTER TABLE public.blood_requests ENABLE ROW LEVEL SECURITY;
CREATE POLICY "requests public read" ON public.blood_requests FOR SELECT USING (true);
CREATE POLICY "requests public insert" ON public.blood_requests FOR INSERT WITH CHECK (true);

CREATE TABLE public.request_donors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id UUID NOT NULL REFERENCES public.blood_requests(id) ON DELETE CASCADE,
  donor_id UUID NOT NULL REFERENCES public.donors(id) ON DELETE CASCADE,
  distance_km DOUBLE PRECISION NOT NULL,
  status public.response_status NOT NULL DEFAULT 'pending',
  responded_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(request_id, donor_id)
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.request_donors TO anon, authenticated;
GRANT ALL ON public.request_donors TO service_role;
ALTER TABLE public.request_donors ENABLE ROW LEVEL SECURITY;
CREATE POLICY "rd public read" ON public.request_donors FOR SELECT USING (true);
CREATE POLICY "rd public insert" ON public.request_donors FOR INSERT WITH CHECK (true);
CREATE POLICY "rd public update" ON public.request_donors FOR UPDATE USING (true) WITH CHECK (true);

CREATE INDEX idx_request_donors_request ON public.request_donors(request_id);
CREATE INDEX idx_request_donors_donor ON public.request_donors(donor_id);
CREATE INDEX idx_donors_bg ON public.donors(blood_group);

ALTER PUBLICATION supabase_realtime ADD TABLE public.request_donors;
ALTER PUBLICATION supabase_realtime ADD TABLE public.blood_requests;
