# TranspTransact

TranspTransact is a minimal viable product (MVP) platform designed to facilitate interactions among three types of companies in business:

1. **Transporters**
2. **Buyers** (bulk purchase)
3. **Sellers** (bulk sale)

## Overview

This project comprises a complete solution, including a front-end, back-end, and a deployed contract on a Gnosis Fork, as well as the implementation of agent logic.

## Project Flow

1. **Order Creation**: 
   - An order is created detailing the products being transported, the distance involved, the payments associated, and the initial and end checkpoints (the route for the truck).
   - Four wallet addresses are designated as 'approvers' for this order.

2. **Truck Tracking**: 
   - A geolocation API (currently mocked for demonstration purposes) tracks the truck's journey. Once it reaches the end checkpoint, its arrival is recorded in the database.

3. **Approval Process**:
   - Upon arrival, the front-end interface allows each of the assigned approvers (from the transporter, buyer, seller, and platform) to mark the transaction as approved.
   - The approvers are the addresses set in the initial order creation.

4. **Agent Responsibilities**:
   The agent performs several critical tasks:
   a. Fetch all unfinalized orders from the back-end.

   b. Check the database for an order hash, which represents the order data saved on IPFS.

   c. If no order hash exists, save the order data to IPFS and upload it to the API.

   d. Each agent verifies whether the party assigned to them (seller, buyer, transporter, or platform) has approved the transaction.

   e. If a majority (3 out of 4) of the parties approve, a transaction is executed. (Initially, there were plans to implement a multisend transaction for the multiple financial transactions involved, but due to time constraints, this feature was not completed.)

## Platform Role

TranspTransact not only acts as a matchmaking service but also serves as a guarantor to ensure that funds reach their intended destination. Approval from at least two of the three parties is required for the transaction to proceed. The platform will conduct its own investigations in the event of a dispute and will not approve transactions without due diligence.
