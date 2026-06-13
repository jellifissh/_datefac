# MinerU Body Package

Purpose:
- Read and normalize MinerU table/body outputs and map them into later structured sidecars.

Not responsible for:
- directly invoking the MinerU CLI

Place new files here when:
- they consume MinerU-generated files such as Markdown and structured JSON and turn them into downstream interpretable records

Category:
- source code

MinerU-first / table-first relation:
- this package is directly tied to the MinerU-first chain because it consumes parse artifacts after MinerU has already run.
