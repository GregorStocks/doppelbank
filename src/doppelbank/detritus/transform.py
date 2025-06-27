import uuid
from datetime import timedelta

from doppelbank.lib.timestamp import format_iso8601_z, parse_iso8601_z
from doppelbank.schemas.bedrock import (
    CardSwipeEvent,
    EventCollection,
    PaycheckEvent,
    TransferEvent,
)
from doppelbank.schemas.detritus import (
    AddCleared,
    AddPending,
    BankEvent,
    BankLedger,
    RemovePending,
)


def bedrock_to_detritus(bedrock_collection: EventCollection) -> BankLedger:
    events = []
    for event in bedrock_collection.events:
        # Check event type using isinstance with Tagged unions
        if isinstance(event, CardSwipeEvent):
            cs = event
            if not cs.timestamp:
                continue  # skip events with empty timestamp

            # AddPending event
            pending_id = str(uuid.uuid4())
            pending_transaction_id = str(uuid.uuid4())
            account_id = cs.account_id
            events.append(
                BankEvent(
                    event_id=pending_id,
                    timestamp=cs.timestamp,
                    event=AddPending(
                        event_id=pending_id,
                        transaction_id=pending_transaction_id,
                        account_id=account_id,
                        amount=cs.amount,
                        description=cs.description,
                        merchant=cs.merchant,
                        category=cs.category,
                    ),
                )
            )
            # AddCleared event (simulate clearing 2 days later)
            cleared_id = str(uuid.uuid4())
            cleared_transaction_id = str(uuid.uuid4())
            cleared_dt = parse_iso8601_z(cs.timestamp) + timedelta(days=2)
            events.append(
                BankEvent(
                    event_id=cleared_id,
                    timestamp=format_iso8601_z(cleared_dt),
                    event=AddCleared(
                        event_id=cleared_id,
                        transaction_id=cleared_transaction_id,
                        account_id=account_id,
                        amount=cs.amount,
                        description=cs.description,
                        merchant=cs.merchant,
                        category=cs.category,
                        pending_event_id=pending_id,
                    ),
                )
            )
            # RemovePending event (after clearing)
            remove_pending_id = str(uuid.uuid4())
            events.append(
                BankEvent(
                    event_id=remove_pending_id,
                    timestamp=format_iso8601_z(cleared_dt),
                    event=RemovePending(
                        event_id=remove_pending_id,
                        transaction_id=pending_transaction_id,
                        account_id=account_id,
                        reason="cleared",
                        related_event_id=cleared_id,
                    ),
                )
            )
        elif isinstance(event, PaycheckEvent):
            pc = event
            if not pc.timestamp:
                continue  # skip events with empty timestamp
            cleared_id = str(uuid.uuid4())
            account_id = pc.account_id
            events.append(
                BankEvent(
                    event_id=cleared_id,
                    timestamp=pc.timestamp,
                    event=AddCleared(
                        event_id=cleared_id,
                        transaction_id=str(uuid.uuid4()),
                        account_id=account_id,
                        amount=pc.amount,
                        description=pc.description,
                        merchant=pc.employer,
                        category="paycheck",
                        pending_event_id="",
                    ),
                )
            )
        elif isinstance(event, TransferEvent):
            tf = event
            if not tf.timestamp:
                continue  # skip events with empty timestamp
            # Outgoing transfer (from_account)
            out_id = str(uuid.uuid4())
            events.append(
                BankEvent(
                    event_id=out_id,
                    timestamp=tf.timestamp,
                    event=AddCleared(
                        event_id=out_id,
                        transaction_id=str(uuid.uuid4()),
                        account_id=tf.from_account,
                        amount=-abs(tf.amount),  # negative for outgoing
                        description=tf.description,
                        merchant="transfer_out",
                        category="transfer",
                        pending_event_id="",
                    ),
                )
            )
            # Incoming transfer (to_account)
            in_id = str(uuid.uuid4())
            events.append(
                BankEvent(
                    event_id=in_id,
                    timestamp=tf.timestamp,
                    event=AddCleared(
                        event_id=in_id,
                        transaction_id=str(uuid.uuid4()),
                        account_id=tf.to_account,
                        amount=abs(tf.amount),  # positive for incoming
                        description=tf.description,
                        merchant="transfer_in",
                        category="transfer",
                        pending_event_id="",
                    ),
                )
            )

    return BankLedger(events=events)
