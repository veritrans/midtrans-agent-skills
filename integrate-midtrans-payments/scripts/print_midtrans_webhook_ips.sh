#!/usr/bin/env bash
# print_midtrans_webhook_ips.sh
#
# Print Midtrans notification source IPs/CIDRs for inbound firewall, WAF,
# and ingress allowlists.
#
# Source: https://docs.midtrans.com/docs/ip-address
# Values can change. Verify current docs before applying production rules.
# Do not use this for outbound calls to Midtrans API domains; docs say to
# allowlist API domain names, not resolved IP addresses.
#
# Usage:
#   ./print_midtrans_webhook_ips.sh                    # all notification sources
#   ./print_midtrans_webhook_ips.sh production         # production new list
#   ./print_midtrans_webhook_ips.sh sandbox            # sandbox new list
#   ./print_midtrans_webhook_ips.sh production-legacy  # production legacy list
#   ./print_midtrans_webhook_ips.sh sandbox-legacy     # sandbox legacy list
#   ./print_midtrans_webhook_ips.sh --as nginx         # nginx allow directives
#   ./print_midtrans_webhook_ips.sh --as csv           # one address/range per line
#
# Exit codes:
#   0  success
#   2  bad input (unknown env or unknown --as format)

set -euo pipefail

production_ips=(
  "8.215.30.222"
  "147.139.209.49"
  "8.215.32.142"
  "147.139.163.77"
  "8.215.25.24"
  "8.215.3.193"
  "147.139.210.20"
  "149.129.238.95"
  "8.215.9.206"
  "147.139.134.22"
  "149.129.253.222"
  "8.215.56.174"
  "8.215.27.65"
  "147.139.129.139"
  "149.129.192.10"
  "8.215.15.117"
  "149.129.234.6"
  "8.215.79.106"
  "149.129.192.204"
  "8.215.83.17"
  "147.139.197.147"
  "147.139.207.105"
  "147.139.193.191"
  "147.139.201.222"
  "8.215.82.175"
  "149.129.218.45"
  "8.215.10.140"
  "8.215.83.130"
  "147.139.206.209"
  "8.215.75.234"
)

sandbox_ips=(
  "149.129.216.115"
  "147.139.167.196"
  "147.139.179.47"
  "147.139.144.184"
  "147.139.169.196"
  "147.139.168.217"
  "8.215.17.96"
  "149.129.254.13"
  "147.139.203.227"
  "147.139.192.94"
  "147.139.206.250"
  "147.139.213.108"
  "8.215.23.167"
  "147.139.209.91"
  "8.215.21.228"
  "147.139.173.83"
  "147.139.132.215"
  "149.129.227.68"
  "149.129.234.77"
  "147.139.137.231"
  "147.139.180.156"
  "8.215.10.65"
  "8.215.22.163"
  "147.139.215.190"
  "8.215.0.89"
  "8.215.16.140"
  "147.139.165.251"
  "147.139.209.83"
  "147.139.167.157"
  "147.139.192.232"
)

production_legacy_ips=(
  "103.208.23.0/24"
  "103.208.23.6/32"
  "103.127.16.0/23"
  "103.127.17.6/32"
  "34.87.92.33"
  "34.87.59.67"
  "35.186.147.251"
  "34.87.157.231"
  "13.228.166.126/32"
  "52.220.80.5/32"
  "3.1.123.95/32"
  "108.136.204.114"
  "108.136.34.95"
  "108.137.159.245"
  "108.137.135.225"
  "16.78.53.66"
  "43.218.2.230"
  "16.78.88.149"
  "16.78.85.64"
  "16.78.69.49"
  "16.78.98.130"
  "16.78.9.40"
  "43.218.223.26"
)

sandbox_legacy_ips=(
  "34.101.68.130"
  "34.101.92.69"
  "34.142.147.133/32"
  "34.142.169.131/32"
  "34.142.231.22/32"
  "35.240.161.215/32"
  "34.142.227.232/32"
  "34.124.184.175/32"
  "35.197.130.2/32"
  "34.142.233.114/32"
)

format="labeled"
target="all"

while (( "$#" )); do
  case "$1" in
    production|sandbox|production-legacy|sandbox-legacy|all)
      target="$1"
      shift
      ;;
    --as)
      shift
      case "${1:-}" in
        labeled|nginx|csv)
          format="$1"
          ;;
        *)
          echo "error: unknown --as format '${1:-}', expected labeled|nginx|csv" >&2
          exit 2
          ;;
      esac
      shift
      ;;
    -h|--help)
      sed -n '/^# Usage/,/^# Exit codes/p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "error: unknown argument '$1'" >&2
      exit 2
      ;;
  esac
done

print_one() {
  local label="$1"
  shift
  local values=("$@")
  case "$format" in
    labeled)
      echo "# $label"
      printf '%s\n' "${values[@]}"
      echo
      ;;
    nginx)
      echo "# $label"
      for value in "${values[@]}"; do
        echo "allow $value;"
      done
      echo
      ;;
    csv)
      printf '%s\n' "${values[@]}"
      ;;
  esac
}

case "$target" in
  production)
    print_one "Midtrans production notification sources" "${production_ips[@]}"
    ;;
  sandbox)
    print_one "Midtrans sandbox notification sources" "${sandbox_ips[@]}"
    ;;
  production-legacy)
    print_one "Midtrans production legacy notification sources" "${production_legacy_ips[@]}"
    ;;
  sandbox-legacy)
    print_one "Midtrans sandbox legacy notification sources" "${sandbox_legacy_ips[@]}"
    ;;
  all)
    print_one "Midtrans production notification sources" "${production_ips[@]}"
    print_one "Midtrans sandbox notification sources" "${sandbox_ips[@]}"
    print_one "Midtrans production legacy notification sources" "${production_legacy_ips[@]}"
    print_one "Midtrans sandbox legacy notification sources" "${sandbox_legacy_ips[@]}"
    ;;
esac

if [[ "$format" == "labeled" || "$format" == "nginx" ]]; then
  echo "# Verify current values before applying production rules:" >&2
  echo "#   https://docs.midtrans.com/docs/ip-address" >&2
  echo "# Always verify webhook signatures; IP allowlists are not authenticity proof." >&2
fi
