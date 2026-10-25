# Work Package 10: Automotive Engineering Quality Challenges & Traceability

## 1. Domain Scope & Mission
Automotive closures and sealing engineering presents intricate physics and multi-domain interactions across structural rigidity, aerodynamic suction, micro-switches, Hall sensors, elastomeric seals, and mechanical wear. This work package validates the end-to-end closed-loop quality lifecycle for five critical failure modes.

## 2. Five Engineering Quality Challenges & Empirical Validation

### Challenge 1: Frameless Door Window Glass Repeatability & Aero Suction Deflection
- **Vehicle Subsystem**: Frameless Window System
- **Engineering Phenomenon**: At vehicle velocities > 140 km/h, the cabin-to-exterior aerodynamic pressure differential exerts an outward suction force (~800 N) across the door glass surface. Inadequate cross-car Y-axis torsional rigidity in the B-pillar lower guide bracket caused a 1.35 mm glass yaw tilt deviation, breaking seal contact and causing severe wind noise (74.2 dB).
- **Quality Lineage**:
  - `Part`: Extruded 6061-T6 Aluminum guide channel (`EP9-WIN-GUIDE-01`).
  - `DFMEA`: High AP risk (`DFMEA-WIN-001`, S=7, O=5, D=4, RPN=140).
  - `DVP&R`: High-speed aeroacoustic wind tunnel & rain blast test (`DVP-WIN-AERO-01`).
  - `Test Run`: Failed execution at 15,000 cycles (`RUN-WIN-AERO-001`).
  - `Issue`: Critical defect logged (`ISS-EP9-WIN-001`).
  - `5-Why Root Cause`: Systemic omission of high-speed dynamic aerodynamic suction loads in bracket structural guidelines.
  - `ECR`: Bracket thickness upgauged from 1.5 mm to 2.2 mm with dual transverse embossed swage ribs (`ECR-EP9-WIN-001`, post_rev `B.0`).
  - `Closed-Loop Verification`: Status `ValidationPass`, re-test verified with zero wind noise and repeat accuracy < 0.35 mm.

### Challenge 2: Regulator Motor Stall Current & Anti-Pinch False Trigger
- **Vehicle Subsystem**: Glass Regulator Module
- **Engineering Phenomenon**: In sub-zero weather conditions (-25°C), EPDM glass run channel friction coefficient increases significantly due to cold glass hardening. The motor controller's static ripple-count anti-pinch threshold misidentified seal resistance as a passenger obstruction, triggering false reversals.
- **Traceability Chain**: Smart DC motor with Hall sensor (`EP9-REG-MOTOR-02`) mapped through temperature-compensated anti-pinch curve verification (FMVSS 118 / ECE R21).

### Challenge 3: Power Tailgate Sealing Water Leak & Corner CLD Deficiency
- **Vehicle Subsystem**: Power Tailgate System & Primary Body Seal
- **Engineering Phenomenon**: High-pressure spray (ISO 20653 IPX9K) penetrated the C-pillar roof gutter corner. 5-Why analysis revealed molded corner joint compression load deflection (CLD) dropped below 2.5 N/cm due to corner radius tooling shrinkage.
- **Remediation**: Tooling modified to insert localized sponge EPDM insert (`EP9-SEAL-TAIL-03`).

### Challenge 4: Door Hinge Sag & Squeak/Rattle under Slam Durability
- **Vehicle Subsystem**: Door Hinge & Check Link
- **Engineering Phenomenon**: Door drop sag > 1.8 mm after 50,000 door slam cycles (QC/T 627). Root cause traced to bronze sinter bushing thickness wearing prematurely.
- **Remediation**: Bushing material upgraded to PTFE-composite self-lubricating bushing (`EP9-HINGE-UPPER-04`, post_rev `B.0`).

### Challenge 5: Multi-Module Cross-Linking & Traceability API
- **API Endpoint**: `GET /api/v1/traceability/lineage/{issue_id}`
- **Automated Verification**:
  - Unbroken graph traversals from Problem -> Part -> DFMEA -> DVPR -> Physical Test Telemetry -> 5-Why -> ECR.
  - Automated gate checking: `closed_loop_verified == True` requires confirmed root cause, approved/implemented ECR, and closed/validation-passed issue.
  - Subsystem aggregation endpoint: `GET /api/v1/traceability/subsystem/{name}` returns real-time risk health metrics and active part trees.
