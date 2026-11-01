# Hardware-Steckbrief Heimrechner

**Ermittelt:** 31.10.2026 (Schritt 1.0a)

| Bereich | Wert |
|---|---|
| Betriebssystem | Windows 11 Pro, Build 26300 |
| CPU | Intel Core i5-13600K (14 Kerne, 20 Threads) |
| RAM | 64 GB, davon rund 31 GB für die Docker-VM |
| GPU | NVIDIA GeForce GTX 1650, 4 GB VRAM, Treiber 610.88 |
| Docker | Docker Desktop 29.9.2 auf WSL 2, Compose 5.6.1, NVIDIA-Runtime vorhanden |
| Speicher | Laufwerk D: 156 GB frei, Laufwerk C: 1,2 TB frei |
| Python | 3.14.5 |

## GPU-Zugriff

- Der Testcontainer sieht die GPU: `docker run --rm --gpus all --entrypoint nvidia-smi ollama/ollama:0.40.13`
- Ollama meldet CUDA mit 3,2 GB verfügbarem VRAM. `bge-m3` läuft zu 100 % auf der GPU und belegt 689 MB.

## Folgen für die Modellwahl

- Neben dem Embedding-Modell bleiben rund 2,5 GB VRAM. Das Scout-Modell für Schritt 1.6b muss dort hineinpassen oder wechselweise geladen werden.
- Gemessener Embedding-Durchsatz mit echten Chunks (ca. 600 Tokens): 1,3 s je Chunk, 352 Chunks in rund 7 Minuten. Ein erster Test mit sehr langen Texten hatte 3,2 s ergeben und war zu pessimistisch.
- Für die Laufzeit von Schritt 1.6 zählt dieser Durchsatz: 10.000 Chunks dauern rund 3,6 Stunden, 100.000 Chunks rund 36 Stunden.

## Parallelbetrieb auf diesem Rechner

`iam-neo4j` belegt 7474 und 7687, außerdem laufen die `bio`-Container. Neolibris nutzt daher 17474 und 17687, siehe `docker-compose.yml`.
