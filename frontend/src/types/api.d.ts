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
