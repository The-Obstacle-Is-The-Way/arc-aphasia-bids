# How to Fix Upload Crashes on Large Datasets

> **Problem**: Upload crashes at 0% with "leaked semaphore" warning
> **Solution**: Use `arc-bids` which has a workaround for the upstream bug

---

## Symptoms

```text
Uploading the dataset shards:   0%|          | 0/902 [00:00<?, ? shards/s]
UserWarning: resource_tracker: There appear to be 1 leaked semaphore objects
[Process killed]
```

The upload crashes at 0% even WITH `num_shards` set.

---

## Root Cause

The `datasets` library has a bug (#7894): when sharding datasets with
`Sequence()` nested types (like `Sequence(Nifti())`), the `embed_table_storage`
function crashes at the C++ level due to Arrow table slice references.

See [Why Uploads Fail](../explanation/why-uploads-fail.md) for full details.

---

## Solution: Use arc-bids CLI

The `arc-bids` package includes a workaround for this upstream bug:

```bash
# Build and upload (with workaround)
uv run arc-bids build data/openneuro/ds004884 \
    --hf-repo hugging-science/arc-aphasia-bids \
    --no-dry-run
```

---

## How It Works

Our `push_dataset_to_hub()` function works around [huggingface/datasets#7894](https://github.com/huggingface/datasets/issues/7894):

1. **Iterates one shard at a time**
2. **Converts to pandas and recreates Dataset** (breaks Arrow slice references)
3. **Embeds NIfTI bytes into Arrow table**
4. **Writes to temporary Parquet file on disk**
5. **Uploads via `HfApi.upload_file(path=...)`**
6. **Deletes temp file before next iteration**

```python
# From src/arc_bids/core.py
for i in range(num_shards):
    shard = ds.shard(num_shards=num_shards, index=i, contiguous=True)

    # WORKAROUND for huggingface/datasets#7894:
    # Break Arrow slice references that crash embed_table_storage
    shard_df = shard.to_pandas()
    fresh_shard = Dataset.from_pandas(shard_df, preserve_index=False)
    fresh_shard = fresh_shard.cast(ds.features)

    # Now embed and write
    table = fresh_shard._data.table.combine_chunks()
    embedded_table = embed_table_storage(table)
    pq.write_table(embedded_table, str(local_parquet_path))

    api.upload_file(path_or_fileobj=str(local_parquet_path), ...)
    local_parquet_path.unlink()  # Free disk
    del fresh_shard, shard_df, shard  # Free RAM
```

---

## If You're Not Using arc-bids

If you need this pattern for a different dataset, copy the approach from
`src/arc_bids/core.py`:

1. Don't use `ds.push_to_hub()` for large datasets with `Sequence()` types
2. Manually shard with `ds.shard()`
3. **Convert shard to pandas and recreate Dataset** (critical!)
4. Embed with `embed_table_storage(table)`
5. Write to Parquet on disk with `pq.write_table()`
6. Upload with `HfApi.upload_file(path=...)` (file path, not bytes)
7. Clean up before next shard

See [UPSTREAM_BUG.md](/UPSTREAM_BUG.md) for full technical details.

---

## When Will This Be Fixed?

We submitted a fix upstream: [PR #7896](https://github.com/huggingface/datasets/pull/7896)

Once merged, you'll be able to use standard `ds.push_to_hub()` without the
workaround. Until then, use `arc-bids` or implement the pandas round-trip
yourself.

---

## Verification

After running the upload, you should see steady progress:

```text
Uploading Shards:  50%|█████     | 451/902 [2:15:30<2:10:00, 8.65s/it]
```

---

## Related

- [Why Uploads Fail](../explanation/why-uploads-fail.md) - Technical explanation
- [Fix Empty Uploads](fix-empty-uploads.md) - Another common issue
- [UPSTREAM_BUG.md](/UPSTREAM_BUG.md) - Upstream bug details
