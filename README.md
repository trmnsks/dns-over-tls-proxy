# DNS over TLS Proxy (DoT)

## About the project

### Problem

As is known DNS resolvers translate human-readable domain names into machine-readable IP addresses.
By default, DNS queries and responses are sent in plaintext (via UDP), which means they can be traced by networks, ISPs, proxies, etc.
This lack of privacy has a huge impact on security and, in some cases, human rights. If DNS queries are not private, then it becomes easier for governments to censor the Internet and for attackers to stalk user's online behavior.

### Solution

Use DNS over TLS standard for encrypting DNS queries to keep them secure and private.

### Implementation

The dot_proxy is a simple daemon that listens on TCP/53 for incoming queries and forwards those to public DNS over TLS. By default, the daemon listens on all interfaces and uses Cloudflare (1.1.1.1:853) DNS resolver.

```text
|        |        TCP/53         |     |       TLS/853       |     |
| Client | <-------------------> | DoT | <-----------------> | DNS |
|        |     (Unencrypted)     |     |     (Encrypted)     |     |
```

Keep in mind that this proxy encrypts only upstream DoT traffic, which means that all traffic from the Client to DoT is unencrypted and could be easily traced by Deep Packet Inspection (DPI) tools. Take this into account when placing the daemon in your infrastructure.

**Technical Notes**:

- The **dot_proxy** module uses the standard **socketserver** framework which acts as an abstraction layer over the standard socket module and simplifies writing network servers.
- The **TCPServer** class extends the standard **socketserver.TCPServer** class to allow initializing a DNS resolver address.
- The **TCPServer** class also extends **socketserver.ThreadingMixIn** class to process each request in a separate thread. This makes it possible to handle multiple clients at the same time and they don't have to wait in queue.
- The **TCPHandler** class extends the standard **socketserver.BaseRequestHandler** class, overrides the **handle** method and realizes the main logic.
- For safety, the buffer is set to 4096 bytes to not cut off messages in case of large queries.
- Based on security considerations SSL context is created with defaults. It will load the system’s trusted CA certificates, enable certificate validation and hostname checking, and try to choose reasonably secure protocol and cipher settings.
- The forwarder (**\_\_get_tls_sock**) is implemented using the standard socket module.

## Getting Started

The solution contains a simple service **dot_proxy.py** and **Dockerfile**.

### Prerequisites

- `Docker >= 20.10.x`

## Usage

### Running the application

Make sure the 53 port on your OS is not in use. For example, Ubuntu has systemd-resolved listening on port 53 by default.

With default options:

1. Build Docker image:

   ```shell
   docker build -t dot-proxy .
   ```

2. Run Docker container:

   ```shell
   docker run -dt -p 53:53/tcp --rm --name dot-proxy dot-proxy
   ```

### Options

The following options could be passed to the container as environment variables:

- **HOST** - local address that is used to listen for incoming queries. Default: 0.0.0.0
- **PORT** - local port that is used to listen for incoming queries. Default: 53
- **DNS_HOST** - DNS resolver address that forwards queries. Default: 1.1.1.1
- **DNS_PORT** - DNS resolver port that forwards queries. Default: 853

#### Examples

1. Run the Docker container and listen to queries on the loopback interface:

   ```shell
   docker run -dt -p 53:53/tcp \
   -e HOST=127.0.0.1 \
   -e PORT=53 --rm --name dot-proxy dot-proxy
   ```

2. Run the Docker container and use Google DNS Resolver:

   ```shell
   docker run -dt -p 53:53/tcp \
   -e DNS_HOST=8.8.8.8 \
   -e DNS_PORT=853 --rm --name dot-proxy dot-proxy
   ```

### Testing

Open 2 terminals:

- Terminal 1:

  ```shell
  docker logs -f dot-proxy
  ```

- Terminal 2:

  ```shell
  dig google.com @127.0.0.1 +vc
  ```

Check the output:

- Terminal 1 - Docker logs:

  ```shell
  -> TCP server started -> IP: ('0.0.0.0', 53)
  -> DNS to forward to -> IP: ('1.1.1.1', 853)
  --> Received msg -> IP: ('172.17.0.1', 48166), BYTES:53
  ---> Connected to -> IP: ('1.1.1.1', 853), TLSv1.3
  ---> Forwarded msg -> IP: 1.1.1.1, BYTES:53
  ---> Received answ -> IP: 1.1.1.1, BYTES:470
  ---> Forwarded answ -> IP: ('172.17.0.1', 48166), BYTES:470
  ```

- Terminal 2 - DiG client:

  ```shell
  ; <<>> DiG 9.16.27-Debian <<>> google.com @127.0.0.1 +vc
  ;; global options: +cmd
  ;; Got answer:
  ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 35251
  ;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

  ;; OPT PSEUDOSECTION:
  ; EDNS: version: 0, flags:; udp: 1232
  ; PAD: (409 bytes)
  ;; QUESTION SECTION:
  ;google.com.                    IN      A

  ;; ANSWER SECTION:
  google.com.             155     IN      A       142.250.200.142

  ;; Query time: 176 msec
  ;; SERVER: 127.0.0.1#53(127.0.0.1)
  ;; WHEN: Sun Nov 12 21:00:30 CET 2022
  ;; MSG SIZE  rcvd: 468
  ```

## Improvements

- Implement UDP Request handler and process TCP and UDP simultaneously.
- Implement the caching mechanism to improve load times and reduce bandwidth/CPU consumption.
- Implement DNS Firewall, for example, content filtering, malware/spam, botnet protection, etc.

## License

Distributed under the MIT License. See `LICENSE` for more information.
