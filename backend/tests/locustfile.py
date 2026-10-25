import random
from locust import HttpUser, task, between

class EQLUser(HttpUser):
    wait_time = between(0.01, 0.05)

    def on_start(self):
        self.client.headers.update({"X-Benchmark": "1"})

    @task(5)
    def view_dashboard(self):
        self.client.get("/api/v1/dashboard/stats", name="[GET] /dashboard/stats")

    @task(4)
    def list_programs(self):
        self.client.get("/api/v1/programs?page=1&page_size=20", name="[GET] /programs")

    @task(4)
    def list_parts(self):
        subsystem = random.choice(["Primary Body Seal", "Glass Regulator Module", "Front Door Closure"])
        self.client.get(f"/api/v1/parts?page=1&page_size=20&subsystem={subsystem}", name="[GET] /parts")

    @task(4)
    def list_dfmea(self):
        ap = random.choice(["High", "Medium", "Low"])
        self.client.get(f"/api/v1/dfmea?page=1&page_size=20&action_priority={ap}", name="[GET] /dfmea")

    @task(3)
    def list_dvpr(self):
        self.client.get("/api/v1/dvpr?page=1&page_size=20&test_phase=DV-A", name="[GET] /dvpr")

    @task(3)
    def list_tests(self):
        self.client.get("/api/v1/tests?page=1&page_size=20&result=Pass", name="[GET] /tests")

    @task(3)
    def list_issues(self):
        self.client.get("/api/v1/issues?page=1&page_size=20&severity=S1-Critical", name="[GET] /issues")

    @task(3)
    def list_changes(self):
        self.client.get("/api/v1/changes?page=1&page_size=20&approval_status=Approved", name="[GET] /changes")

    @task(2)
    def search_knowledge(self):
        kw = random.choice(["seal", "water", "pinch", "door", "glass"])
        self.client.get(f"/api/v1/knowledge?search={kw}", name="[GET] /knowledge")

    @task(2)
    def query_traceability_lineage(self):
        issue_id = random.randint(1, 20)
        self.client.get(f"/api/v1/traceability/lineage/{issue_id}", name="[GET] /traceability/lineage")

    @task(1)
    def create_program_stress(self):
        rnd = random.randint(100000, 999999)
        self.client.post("/api/v1/programs", json={
            "code": f"LOCUST-P-{rnd}",
            "name": f"Stress Program {rnd}",
            "platform": "BEV-800V",
            "phase": "Proto-A",
            "lead_engineer": "Locust Tester",
            "quality_manager": "QM Specialist"
        }, name="[POST] /programs")
