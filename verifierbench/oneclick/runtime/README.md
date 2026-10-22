# VerifierBench aligned execution runtime

This is a derived execution-only distribution of the supplied VerifierBench runtime
and the reviewed suiteenv integration fixes. It contains no historical scoring
records or model table values. Original runner, capability and paper_score.aggregate
source bytes are preserved; frozen task membership, candidate hashes and round
policy are unchanged. The runner is used only with new result directories.

Dataset files are downloaded by the suite bootstrap from the pinned Hugging Face
repository into dataset/. AppWorld protected material is reconstructed on the target
host from upstream encrypted distributions, never shipped as plaintext here.

Do not invoke scripts/paper_score.py without fresh records: its preserved historical
CLI cannot operate on this results-free distribution. The one-click report entrypoint
calls aggregate with an explicit current-run freeze and only newly generated receipts.

MANIFEST.json covers vendored files. Bootstrap seals a separate final manifest after
merging the verified HF dataset and binds its SHA into all new generated artifacts.
Do not reuse artifacts from other runtime manifests. Original third-party terms remain
applicable; licenses/ contains the dataset notices supplied by the release.
