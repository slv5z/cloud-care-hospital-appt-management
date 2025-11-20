# TODO: Fix Cancelled Appointments Display

## Approved Plan
Change patient cancellation logic to set appointment status to "Cancelled" instead of deleting the record, so that cancelled appointments appear in the "view cancelled appointments" page.

## Steps
- [x] Modify the `/patient/cancel_appointment` POST endpoint in main.py to update appointment status to "Cancelled" instead of deleting the record.
- [x] Verify the change by checking the code and ensuring consistency with admin cancellation.
- [x] Task completed: Patient cancellations now set status to "Cancelled", matching admin behavior.
