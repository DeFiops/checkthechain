from __future__ import annotations

import typing

from ctc import rpc
from ctc import spec

from .. import block_crud
from .. import block_normalize


async def async_get_block_timestamp(
    block: spec.BlockReference,
    provider: spec.ProviderSpec = None,
    use_db: bool = True,
) -> int:

    if isinstance(block, int) and use_db:
        from ctc import db

        network = rpc.get_provider_network(provider)
        engine = db.create_engine(datatype='block_timestamps', network=network)
        if engine is not None:
            with engine.connect() as conn:
                timestamp = await db.async_query_block_timestamp(
                    conn=conn,
                    block_number=block,
                )
                if timestamp is not None:
                    return timestamp

    block_data = await block_crud.async_get_block(block, provider=provider)
    return block_data['timestamp']


async def async_get_block_timestamps(
    blocks: typing.Sequence[spec.BlockReference],
    include_full_transactions: bool = False,
    chunk_size: int = 500,
    provider: spec.ProviderSpec = None,
    use_db: bool = True,
) -> list[int]:

    blocks = await block_normalize.async_block_numbers_to_int(
        blocks=blocks,
        provider=provider,
    )

    # get timestamps from db
    if use_db:
        from ctc import db

        network = rpc.get_provider_network(provider)
        engine = db.create_engine(datatype='block_timestamps', network=network)
        if engine is not None:
            with engine.connect() as conn:
                db_timestamps = await db.async_query_block_timestamps(
                    conn=conn,
                    block_numbers=blocks,
                )
            results = dict(zip(blocks, db_timestamps))
            remaining_blocks = [
                block
                for block, timestamp in zip(blocks, db_timestamps)
                if timestamp is None
            ]
        else:
            results = {}
            remaining_blocks = blocks
    else:
        results = {}
        remaining_blocks = blocks

    # get timestamps from rpc
    if len(remaining_blocks) > 0:
        node_blocks = await block_crud.async_get_blocks(
            blocks=remaining_blocks,
            include_full_transactions=include_full_transactions,
            chunk_size=chunk_size,
            provider=provider,
        )
        for block_data in node_blocks:
            results[block_data['number']] = block_data['timestamp']

    output: list[int] = []
    for block in blocks:
        result = results[block]
        if result is None:
            raise Exception('failed to get timestamp for block: ' + str(block))
        output.append(result)
    return output
