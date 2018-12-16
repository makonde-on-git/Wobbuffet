"""Create 64bit unique IDs with timestamps embedded."""

import time

# 13 Dec 2018 20:42:00 GMT
WOBBUFFET_EPOCH = 1544733720


def to_timestamp(_id):
    _id = _id >> 22         # strip the lower 22 bits
    _id += WOBBUFFET_EPOCH  # adjust for wobbuffet epoch
    _id = _id // 1000       # convert from milliseconds to seconds
    return _id


def create():
    """Create and return snowflake for current time."""
    def sleep(x): return time.sleep(x/1000.0)
    worker_id = 1
    data_center_id = 1
    worker_id_bits = 5
    data_center_id_bits = 5
    max_worker_id = -1 ^ (-1 << worker_id_bits)
    max_data_center_id = -1 ^ (-1 << data_center_id_bits)
    sequence_bits = 12
    worker_id_shift = sequence_bits
    data_center_id_shift = sequence_bits + worker_id_bits
    timestamp_left_shift = sequence_bits + worker_id_bits + data_center_id_bits
    sequence_mask = -1 ^ (-1 << sequence_bits)

    assert 0 <= worker_id <= max_worker_id
    assert 0 <= data_center_id <= max_data_center_id

    last_timestamp = -1
    sequence = 0

    while True:
        timestamp = int(time.time()*1000)
        if last_timestamp > timestamp:
            # clock is moving backwards. waiting until last_timestamp
            sleep(last_timestamp-timestamp)
            continue

        if last_timestamp == timestamp:
            sequence = (sequence + 1) & sequence_mask
            if sequence == 0:
                # sequence overrun
                sequence = -1 & sequence_mask
                sleep(1)
                continue
        else:
            sequence = 0

        last_timestamp = timestamp

        yield (
            ((timestamp-WOBBUFFET_EPOCH) << timestamp_left_shift) |
            (data_center_id << data_center_id_shift) |
            (worker_id << worker_id_shift) |
            sequence)
