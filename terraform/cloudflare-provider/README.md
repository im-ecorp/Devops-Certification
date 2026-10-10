# Cloudflare Provider Practice: Diverse DNS Records

Learn the Terraform lifecycle by managing diverse DNS records (A, CNAME, TXT, MX) in an existing Cloudflare zone. 

## 1. Real Test Setup (Using a Real API Token & Domain)

To apply this to a real Cloudflare account, you need:
1. **A Real Domain:** Already active in your Cloudflare account.
2. **The Zone ID:** Found on the Cloudflare Dashboard -> Domain -> Overview (right sidebar).
3. **An API Token:** Create one at Profile -> API Tokens. Use the **Edit zone DNS** template and restrict it to your practice domain.

**Configure Variables:**
Copy the example variables file:
```bash
cp terraform.tfvars.example terraform.tfvars
```
Edit `terraform.tfvars` and replace `zone_id` and `domain` with your real ones.

**Export the Token:**
Provide the token securely in your shell environment:
```bash
read -rsp "Cloudflare API token: " CLOUDFLARE_API_TOKEN
printf '\n'
export CLOUDFLARE_API_TOKEN
```
*(Never write the API token inside `main.tf` or `terraform.tfvars`)*

**Initialize:**
```bash
terraform init
```

---

## 2. Create Records

Review what Terraform will build:
```bash
terraform plan
```
Expect **4 to add** (A, CNAME, TXT, MX). If the plan looks correct, create the records:

```bash
terraform apply
```
Type `yes` when prompted. After it finishes, check your Cloudflare Dashboard -> DNS. You will see the new `tf-a`, `tf-cname`, `tf-txt`, and `tf-mx` records.

---

## 3. Update Records

To update existing records, change the code or variables, then apply again.

**Example: Update IP & TTL**
1. Edit `terraform.tfvars` and change `ipv4_address` to `"192.0.2.20"`.
2. Change `ttl` to `600`.
3. Check the plan to see the updates in-place:
```bash
terraform plan
```
Expect **0 to add, 4 to change, 0 to destroy** (ttl propagates to all records; IP to A record).
4. Apply the update:
```bash
terraform apply
```

**Example: Change a Record Type or Name**
If you modify `main.tf` and change the `tf-a` record's name to `tf-new-a.${var.domain}`, Terraform will destroy the old record and create the new one. Check this via `terraform plan`.

---

## 4. Delete Records

When you are done testing, clean up the records so they don't litter your domain.

**Delete a single record:**
Delete or comment out the `practice_mx` resource block from `main.tf`, then run `terraform apply`. Terraform detects the missing code and deletes just that record.

**Delete everything (Clean up the lab):**
Run the destroy command to remove all infrastructure managed by this directory:
```bash
terraform destroy
```
Type `yes`. All 4 test records will be removed from Cloudflare.
