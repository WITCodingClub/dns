# Wentworth Coding Club DNS

[![test](https://github.com/witcc/dns/workflows/test/badge.svg)](https://github.com/witcc/dns/actions?query=workflow%3Atest)
[![deploy](https://github.com/witcc/dns/workflows/deploy/badge.svg)](https://github.com/witcc/dns/actions?query=workflow%3Adeploy)

This repository is used for managing the Wentworth Coding Club's DNS configuration through [OctoDNS](https://github.com/octodns/octodns). OctoDNS enables version-controlled, automated DNS management with validation and testing before changes go live.

## Managed Domains

- **witcc.dev** - Primary club domain
- **hackwit.org** - For HackWIT Hackathon

## Adding a Subdomain

### Step 1: Fork the Repository

[Create a fork](https://docs.github.com/en/free-pro-team@latest/github/getting-started-with-github/fork-a-repo) of this repository to your GitHub account.

### Step 2: Edit the Domain Configuration File

Open either [witcc.dev.yaml](./witcc.dev.yaml) or [hackwit.org.yaml](./hackwit.org.yaml) depending on which domain you want to add a subdomain to.

Add the following entry alphabetically based on the subdomain name:

```yaml
SUBDOMAIN_NAME: # yourwitemail@wit.edu
  - ttl: 600
    type: CNAME
    value: SOURCE_DOMAIN_OR_IP.
```

### Step 3: Configure Your Subdomain

- **SUBDOMAIN_NAME**: Replace with your desired subdomain name
  - Example: `hello` would create `hello.witcc.dev`
- **SOURCE_DOMAIN_OR_IP**: Replace with the target domain or IP address
  - For domains: Use `CNAME` and include the trailing `.`
    - Example: `example.com.`
  - For IP addresses: Change `type: CNAME` to `type: A` and remove the trailing `.`
    - Example: `192.0.2.1`
- **Contact info**: Add your wit email in a comment above your entry. This way we know who is responsible for the subdomain. If you're making the PR but it makes more sense for someone else to "own" the subdomain, you can add their email there instead. Feel free to list multiple people.

### Example Configurations

#### CNAME Record (Domain)
```yaml
myproject: # mayonej@wit.edu
  - ttl: 600
    type: CNAME
    value: myproject.vercel.app.
```

#### A Record (IP Address)
```yaml
server: # lambertl@wit.edu
  - ttl: 600
    type: A
    value: 192.0.2.1
```

#### Multiple Records
```yaml
docs: # team@hackwit.org, mayonej@wit.org, lambertl@wit.edu
  - ttl: 600
    type: CNAME
    value: docs-site.netlify.app.
  - ttl: 600
    type: TXT
    value: "verification-token-here"
```

### Step 4: Submit Pull Request

1. Commit your changes to your fork
2. [Create a pull request](https://docs.github.com/en/free-pro-team@latest/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork) back to the main repository
3. Wait for a maintainer to review your PR

**Note**: If changes are requested, update your existing PR by committing to your fork rather than closing and creating a new one.

## Common Record Types

| Type | Usage | Example |
|------|-------|---------|
| **A** | Points to an IPv4 address | `value: 192.0.2.1` |
| **AAAA** | Points to an IPv6 address | `value: 2001:0db8::1` |
| **CNAME** | Points to another domain | `value: example.com.` |
| **TXT** | Text records (verification, SPF, etc.) | `value: "verification-string"` |
| **MX** | Mail server records | See email configuration |



## Testing Changes Locally

If you want to validate your changes before submitting a PR:

### Prerequisites

```bash
# Install Python 3 and pip
# Install OctoDNS and the Cloudflare provider
pip install 'octodns>=1.5.0' octodns-cloudflare
```

### Validate Configuration

```bash
# Run a dry-run to check for errors
./bin/dry-run
```

This will validate your YAML syntax and check for DNS configuration errors without making any actual changes.

## How It Works

1. **Configuration**: DNS records are defined in YAML files (witcc.dev.yaml, hackwit.org.yaml)
2. **Validation**: GitHub Actions automatically validates changes on every PR
3. **Review**: A maintainer reviews and approves your changes
4. **Deployment**: Upon merge to main, changes are automatically deployed to Cloudflare
5. **Propagation**: DNS changes typically propagate within minutes but can take up to 24 hours

## Project Eligibility

Subdomains are available for:
- Official Wentworth Coding Club projects
- Club-affiliated events and initiatives

For questions about eligibility, reach out to a club E-Board member on discord.

## Need Help?

- Check the [OctoDNS documentation](https://github.com/octodns/octodns)
- Open an issue in this repository
- Ask in the club's Discord
- Contact a repository maintainer (primarilly @jaspermayone)

## Contributing

We welcome contributions! Please:
- Follow the existing format and alphabetical ordering
- Include your contact information in comments
- Provide a clear description in your PR
- Be responsive to review feedback

---