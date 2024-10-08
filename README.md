# 0din

Decentralized Federated File Hosting Platform
## Overview

0din is an early alpha-stage, decentralized, federated file hosting platform that aims to provide a scalable and user-friendly solution for sharing and accessing files across a distributed network. By combining the strengths of decentralization and federation, 0din creates a dynamic, resilient ecosystem for file-sharing.

For further details and guides, check out our wiki [here](https://0din.dns-cloud.net/x/guides.html).

## Installation

You have 2 options for installation, either manually or with Docker, Docker is the recommended method.

### Installing using docker

Just use this image, it is currently the only official Docker image for 0din, everything else is not official.

```bash
docker pull pastagringo/0din-docker
```

### Manual Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/4rtemis-4rrow/0din.git

   cd 0din

2. **Create and activate a virtual environment**:
   
   Run the following command in your project directory to create a virtual environment:
   ```bash
   python3 -m venv .venv
   ```

   To activate the virtual environment, execute one of the following commands:
   
   On macOS and Linux:
   ```bash
   source .venv/bin/activate
   ```

   On Windows:
   ```bash
   .venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt

5. **Run the application:**:
   ```bash
   python 0din.py
## Key Features

Decentralized Hosting: Operates on a distributed network of nodes, each contributing to the overall system, ensuring robustness and redundancy.

Federated Architecture: Nodes communicate and interact seamlessly, enabling users to access files hosted on any participating node.

Admin-Only Uploads: File uploads are restricted to administrators. Uploads are done by manually placing files into designated directories rather than through a web interface.

Automatic Categorization: Files are automatically categorized based on their path and file extension, simplifying file organization and retrieval.

HTTP Access: Files can be accessed via standard HTTP, allowing users to browse and download files using any web browser without the need for specialized clients, unlike torrents.

Ease of Setup: Designed for simplicity, 0din is extremely easy to set up, requiring minimal configuration and maintenance.

## How It Works

Setup: Configure 0din by pointing it to a specific directory on your system. 0din will begin hosting files from this directory immediately.

File Access: Users can search and download files from any node in the network using a standard web browser. The federated design ensures that files are available across the network.

File Management: Administrators manage file uploads by manually placing files into the appropriate directories on their node.

Network Expansion: As more users establish 0din nodes, the network grows, increasing the availability and distribution of files across a broader range.

## Advantages of 0din Over Other Decentralized Solutions

1. Decentralized File Hosting with Federated Search
- 0din: Each node operates independently, hosting its own files and handling its own search queries. The federated search system aggregates results from multiple nodes, ensuring a comprehensive search experience without relying on a central tracker or indexer.
   
- BitTorrent/IPFS: Typically rely on centralized or semi-centralized trackers (BitTorrent) or distributed hash tables (IPFS) for indexing and search.

2. Simple Node Operation
- 0din: Nodes are lightweight and easy to set up, requiring only a simple configuration and basic file placement. No complex software or additional components are needed for hosting files or participating in the network.
- BitTorrent/IPFS: Can involve more complex setup processes and require additional software or configurations to function effectively.

3. No Need for Specialized Clients
- 0din: Operates over standard HTTP, allowing users to access and download files using any modern web browser. This eliminates the need for specialized clients or software.
- BitTorrent: Requires specific torrent clients to download files. IPFS requires IPFS clients or gateways for accessing content.

4. Rapidly Growing Network with Minimal Overhead
- 0din: Designed to scale effortlessly with the number of nodes, leveraging federated search to distribute query load and minimize individual node responsibilities.
- BitTorrent/IPFS: May experience performance issues with high numbers of peers or files, especially if nodes become heavily loaded with both data and queries.

5. Flexible File Access and Distribution
- 0din: Provides unrestricted access to files, with users able to download from any node hosting the desired content. There are no built-in restrictions on file availability.
- BitTorrent/IPFS: Often involve mechanisms for rate-limiting, seeding requirements, or access controls, which can restrict file availability and download speeds.

6. Admin-Controlled Content Compliance
- 0din: Content compliance is managed by individual node admins, who are responsible for handling copyright and DMCA issues according to their local regulations. This decentralized approach allows flexibility in content management.
- BitTorrent/IPFS: Content management is less flexible, with issues often handled by central entities or through network-wide policies.

7. Autocategorization Based on Path and Extension
- 0din: Automatically categorizes files based on their directory path and file extension, simplifying the organization and searchability of large datasets.
- BitTorrent/IPFS: Generally do not include built-in categorization features, relying on external metadata or user-added tags.

8. Efficient Peer Discovery
- 0din: Utilizes gossip-based peer discovery with a constant heartbeat ping to maintain an up-to-date list of active nodes, ensuring efficient network operation and node management.
- BitTorrent: Depends on trackers or DHT for peer discovery, which can be subject to central points of failure or inefficiencies. IPFS uses a similar DHT-based approach.

9. Community-Driven Expansion
- 0din: Leverages the contributions of data hoarders who bring substantial storage capacities to the network, creating a massive, distributed archive of information.
- BitTorrent/IPFS: Expansion often depends on broader adoption and community support, with no specific focus on data hoarders or large-scale individual contributions.

## Roadmap
### Minor Features

Wiki and Usage Documentation: Comprehensive wiki and usage documents to assist users in setting up and utilizing 0din effectively.

Improved Categorization: More categories, better matching

more controls on the admin panel: like triggering indexing for example, and progress bars for currently running tasks

### Major Features

Proxying Nodes: Support for proxying one node over another, which is useful for nodes that cannot directly port forward, allowing for greater flexibility in network setup.

File Previews: previewing some files in the search page

## Status

0din is currently in early alpha. While the core features are functional, the project is still under development and is not yet ready for production use. We welcome feedback and contributions as we work towards a stable release.

## How to Reach Us

We welcome feedback and contributions! You can connect with us on the following channels:

- **Discord**: You can [join the 0din Discord server](https://discord.gg/WCR7D8xK2s).

- **GitHub Discussions**: Join the conversation, ask questions, and share ideas in our [GitHub Discussions](https://github.com/4rtemis-4rrow/0din/discussions).

