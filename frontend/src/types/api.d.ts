export interface CodeValidateRequest {
  code: string;
}

export interface CodeValidateResponse {
  valid: boolean;
  participation_id: string;
}

export interface ParticipantRegisterRequest {
  code: string;
  full_name: string;
  email: string;
  phone?: string;
  consent_legal: boolean;
  consent_marketing: boolean;
}

export interface ParticipantRegisterResponse {
  participant_id: string;
  participation_id: string;
}

export interface PrizeItem {
  id: string;
  name: string;
  description?: string;
  available: boolean;
}

// --- Spin / Roulette ---
export interface SpinRequest {
  participation_id: string;
}

export interface SpinResult {
  spin_id: string;
  participation_id: string;
  won: boolean;
  prize_id: string | null;
  prize_name: string | null;
  prize_description: string | null;
  segment_index: number; // 0-based index del segmento ganador en la ruleta
}

// --- Admin ---
export interface AdminStats {
  total_participations: number;
  winners_by_category: Record<string, number>;
  total_winners: number;
  total_prizes_remaining: number;
}

export interface AdminPrize {
  id: string;
  name: string;
  description: string | null;
  category: string;
  stock_total: number;
  stock_remaining: number;
  is_active: boolean;
}

export interface FraudFlag {
  id: string;
  participation_id: string;
  participant_name: string;
  participant_email: string;
  reason: string;
  created_at: string;
  invalidated: boolean;
}

export interface FraudListResponse {
  items: FraudFlag[];
  total: number;
  page: number;
  page_size: number;
}
