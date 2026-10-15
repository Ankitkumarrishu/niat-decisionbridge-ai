-- Seed verified knowledge documents (public sources only)
-- Re-run safe: deletes demo rows and re-inserts knowledge by title

DELETE FROM knowledge_documents WHERE title LIKE '[KB]%';

INSERT INTO knowledge_documents (title, category, content, source_url, last_verified_date, verification_status, campus_or_university_id) VALUES
('[KB] NIAT identity and disclaimer', 'general',
 'NIAT is not a university or a degree-awarding body. NIAT is an upskilling initiative by NxtWave. Admission into universities where the NIAT upskilling program is offered is solely at the discretion of the university based on its established admission policies.',
 'https://www.niatindia.com/campus', '2026-03-15', 'verified', NULL),

('[KB] Program availability geography', 'campus',
 'NIAT''s upskilling program is described as available at 35+ institutions across 15 cities in India. Specific collaborating institutions are listed on the campus page; availability varies by institution and city.',
 'https://www.niatindia.com/campus', '2026-03-15', 'verified', NULL),

('[KB] Homepage program positioning', 'curriculum',
 'NIAT describes an industry-ready upskilling journey focused on areas such as AI/ML, robotics, and data science, offered in collaboration with UGC-recognised institutions. Marketing outcomes on the site include disclaimers that outcomes may reflect multiple NxtWave programs.',
 'https://www.niatindia.com/', '2026-03-15', 'verified', NULL),

('[KB] Contact and support channels', 'general',
 'Listed contact: WhatsApp +91 8008 9009 08 (WhatsApp only), email support@niatindia.com. Address: NIAT, No. 144 Survey 37, Financial District, Nanakramguda, Telangana 500032.',
 'https://www.niatindia.com/', '2026-03-15', 'verified', NULL),

('[KB] Application portal', 'admission',
 'Prospective students can use the NAT application flow via apply.niatindia.com. Specific eligibility, fees, and deadlines must be confirmed on the application portal or with NIAT counsellors.',
 'https://apply.niatindia.com/', '2026-03-15', 'verified', NULL),

('[KB] Placement disclaimer', 'placements',
 'NIAT/NxtWave placement-related pages state that enrollment does not assure a job or internship, and outcomes depend on learner effort, skills, and performance. Company hiring numbers may aggregate multiple NxtWave programs.',
 'https://www.niatindia.com/', '2026-03-15', 'verified', NULL),

('[KB] IIT Kharagpur micro-specialisation disclaimer', 'curriculum',
 'IIT Kharagpur provides specific micro-specialisation course(s) to students of the NIAT upskilling program through its Outreach Course Network. The Industry Ready Certificate for the upskilling program is awarded solely by NIAT. IIT Kharagpur does not award, co-award, or endorse NIAT certification.',
 'https://www.niatindia.com/', '2026-03-15', 'verified', NULL);

-- Synthetic demo leads (clearly marked; no real PII)
-- Only insert if no demo leads exist
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM leads WHERE is_demo = true LIMIT 1) THEN
    INSERT INTO leads (
      student_first_name, email, education_status, preferred_location, preferred_campus,
      budget_range, primary_concern, additional_question, preferred_language,
      consent_storage, consent_storage_at, consent_followup, consent_followup_at,
      follow_up_status, application_status, is_demo,
      experiment_group, experiment_enrolled_at, is_eligible_lead, brief_generated_at,
      application_completed_at, source_identifier, campaign_identifier, primary_objection
    ) VALUES
    ('Demo Student A', 'demo.a@example.invalid', 'completed_class_12', 'Telangana', 'SMR University Hyderabad',
     '5_10_lakh', 'fees', 'Is the upskilling fee separate from university tuition?', 'en',
     true, now() - interval '5 days', true, now() - interval '5 days',
     'follow_up_requested', 'not_started', true,
     'treatment', now() - interval '5 days', true, now() - interval '5 days',
     NULL, 'demo_seed', 'growth_hack_demo', 'fees'),

    ('Demo Student B', NULL, 'in_class_12', 'Tamil Nadu', NULL,
     'undecided', 'degree_university', 'Which university awards the B.Tech degree?', 'hi',
     true, now() - interval '3 days', false, NULL,
     'brief_generated', 'not_started', true,
     'control', now() - interval '3 days', true, now() - interval '3 days',
     NULL, 'demo_seed', 'growth_hack_demo', 'degree_university'),

    ('Demo Student C', 'demo.c@example.invalid', 'other', 'Delhi NCR', 'Noida International University',
     'above_10_lakh', 'placements', NULL, 'en',
     true, now() - interval '10 days', true, now() - interval '9 days',
     'application_completed', 'completed', true,
     'treatment', now() - interval '10 days', true, now() - interval '10 days',
     now() - interval '8 days', 'demo_seed', 'growth_hack_demo', 'placements');
  END IF;
END $$;
