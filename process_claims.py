import sys

# Legacy insurance claim processor.
# Reads a CSV of claims and prints the total approved amount per policy.

claims = []


def load(path):
    f = open(path)
    lines = f.readlines()
    f.close()
    for i in range(len(lines)):
        if i == 0:
            continue
        line = lines[i]
        line = line.replace("\n", "")
        parts = line.split(",")
        row = {}
        row["claim_id"] = parts[0]
        row["policy_number"] = parts[1]
        row["claimant_name"] = parts[2]
        row["claim_amount"] = parts[3]
        row["claim_date"] = parts[4]
        row["status"] = parts[5]
        claims.append(row)


def get_policies():
    policies = []
    for c in claims:
        found = False
        for p in policies:
            if p == c["policy_number"]:
                found = True
        if found == False:
            policies.append(c["policy_number"])
    return policies


def total_for_policy(policy):
    total = 0
    for c in claims:
        if c["policy_number"] == policy:
            if c["status"] == "approved":
                total = total + float(c["claim_amount"])
    return total


def main():
    path = "data/sample_claims.csv"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    load(path)
    policies = get_policies()
    report = ""
    for p in policies:
        t = total_for_policy(p)
        report = report + p + ": " + str(t) + "\n"
    print(report)


main()
