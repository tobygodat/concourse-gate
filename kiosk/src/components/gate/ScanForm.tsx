import { useState, type FormEvent } from "react";
/** Ticket ID entry that works with a keyboard-wedge barcode scanner or typing. */
export function ScanForm({
  disabled,
  onScan,
}: {
  disabled: boolean;
  onScan: (ticketId: string) => void;
}) {
  const [value, setValue] = useState("");
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!value.trim()) return;
    onScan(value.trim());
    setValue("");
  };
  return (
    <form className="scan-form" onSubmit={submit}>
      <input
        autoFocus
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Scan or type ticket ID"
        aria-label="Ticket ID"
        disabled={disabled}
      />
      <button type="submit" className="primary" disabled={disabled || !value.trim()}>
        Look up
      </button>
    </form>
  );
}
