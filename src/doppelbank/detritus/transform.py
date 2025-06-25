import uuid
from datetime import timedelta

from doppelbank.lib.timestamp import format_iso8601_z, parse_iso8601_z
from generated.bedrock import EventCollection
from generated.detritus import (
    AddCleared,
    AddPending,
    BankEvent,
    BankLedger,
    RemovePending,
)


def bedrock_to_detritus(bedrock_collection: EventCollection) -> BankLedger:
    events = []
    for event in bedrock_collection.events:
        # Check which event type is set by looking at the actual data
        if (
            event.card_swipe and event.card_swipe.user_id
        ):  # Check if card_swipe has actual data
            cs = event.card_swipe
            if not cs.timestamp:
                continue  # skip events with empty timestamp

            # AddPending event
            pending_id = str(uuid.uuid4())
            pending_transaction_id = str(uuid.uuid4())
            account_id = getattr(
                cs, "account_id", "acc_dummy"
            )  # Use account_id if present
            events.append(
                BankEvent(
                    event_id=pending_id,
                    timestamp=cs.timestamp,
                    add_pending=AddPending(
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
                    add_cleared=AddCleared(
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
                    remove_pending=RemovePending(
                        event_id=remove_pending_id,
                        transaction_id=pending_transaction_id,
                        account_id=account_id,
                        reason="cleared",
                        related_event_id=cleared_id,
                    ),
                )
            )
        elif (
            event.paycheck and event.paycheck.user_id
        ):  # Check if paycheck has actual data
            pc = event.paycheck
            if not pc.timestamp:
                continue  # skip events with empty timestamp
            cleared_id = str(uuid.uuid4())
            account_id = getattr(pc, "account_id", "acc_dummy")
            events.append(
                BankEvent(
                    event_id=cleared_id,
                    timestamp=pc.timestamp,
                    add_cleared=AddCleared(
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
        elif (
            event.transfer and event.transfer.user_id
        ):  # Check if transfer has actual data
            tf = event.transfer
            if not tf.timestamp:
                continue  # skip events with empty timestamp
            # Outgoing transfer (from_account)
            out_id = str(uuid.uuid4())
            events.append(
                BankEvent(
                    event_id=out_id,
                    timestamp=tf.timestamp,
                    add_cleared=AddCleared(
                        event_id=out_id,
                        transaction_id=str(uuid.uuid4()),
                        account_id=tf.from_account or "acc_dummy",
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
                    add_cleared=AddCleared(
                        event_id=in_id,
                        transaction_id=str(uuid.uuid4()),
                        account_id=tf.to_account or "acc_dummy",
                        amount=abs(tf.amount),  # positive for incoming
                        description=tf.description,
                        merchant="transfer_in",
                        category="transfer",
                        pending_event_id="",
                    ),
                )
            )

    return BankLedger(events=events)
