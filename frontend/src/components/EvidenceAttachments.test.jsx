/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 * Copyright (C) 2026 Spyridon Drakopoulos
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import EvidenceAttachments from "./EvidenceAttachments";
import * as api from "../api";

vi.mock("../api");

const ATTACHMENTS = [
  { id: 1, filename: "receipt.pdf", size_bytes: 2048 },
];

beforeEach(() => {
  vi.resetAllMocks();
  api.listAttachments.mockResolvedValue(ATTACHMENTS);
  api.attachmentDownloadUrl.mockImplementation(
    (caseId, evidenceId, id) => `/api/cases/${caseId}/evidence/${evidenceId}/attachments/${id}/download`
  );
});

describe("EvidenceAttachments", () => {
  it("renders existing attachments with a download link", async () => {
    render(<EvidenceAttachments caseId={1} evidenceId={2} canEdit={false} />);

    const link = await screen.findByRole("link", { name: "receipt.pdf" });
    expect(link).toHaveAttribute(
      "href",
      "/api/cases/1/evidence/2/attachments/1/download"
    );
    expect(screen.getByText("2.0 KB")).toBeInTheDocument();
  });

  // Permission-sensitive: a viewer (canEdit=false) must not get an upload
  // control or a way to delete someone else's attachment.
  it("hides the upload input and remove buttons when canEdit is false", async () => {
    render(<EvidenceAttachments caseId={1} evidenceId={2} canEdit={false} />);
    await screen.findByText("receipt.pdf");

    expect(screen.queryByLabelText("Attach file")).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/remove receipt.pdf/i)).not.toBeInTheDocument();
  });

  it("shows the upload input and remove buttons when canEdit is true", async () => {
    render(<EvidenceAttachments caseId={1} evidenceId={2} canEdit={true} />);
    await screen.findByText("receipt.pdf");

    expect(screen.getByLabelText("Attach file")).toBeInTheDocument();
    expect(screen.getByLabelText(/remove receipt.pdf/i)).toBeInTheDocument();
  });

  it("renders nothing when there are no attachments and canEdit is false", async () => {
    api.listAttachments.mockResolvedValue([]);
    const { container } = render(
      <EvidenceAttachments caseId={1} evidenceId={2} canEdit={false} />
    );

    await waitFor(() => expect(api.listAttachments).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  it("uploads the chosen file and refreshes the list", async () => {
    const user = userEvent.setup();
    api.uploadAttachment.mockResolvedValue({ id: 2, filename: "new.png" });
    render(<EvidenceAttachments caseId={1} evidenceId={2} canEdit={true} />);
    await screen.findByText("receipt.pdf");

    const file = new File(["hello"], "new.png", { type: "image/png" });
    await user.upload(screen.getByLabelText("Attach file"), file);

    await waitFor(() => {
      expect(api.uploadAttachment).toHaveBeenCalledWith(1, 2, file);
    });
    expect(api.listAttachments).toHaveBeenCalledTimes(2);
  });

  it("deletes an attachment and refreshes the list", async () => {
    const user = userEvent.setup();
    api.deleteAttachment.mockResolvedValue(undefined);
    render(<EvidenceAttachments caseId={1} evidenceId={2} canEdit={true} />);
    await screen.findByText("receipt.pdf");

    await user.click(screen.getByLabelText(/remove receipt.pdf/i));

    await waitFor(() => {
      expect(api.deleteAttachment).toHaveBeenCalledWith(1, 2, 1);
    });
    expect(api.listAttachments).toHaveBeenCalledTimes(2);
  });

  it("shows an error if upload fails", async () => {
    const user = userEvent.setup();
    api.uploadAttachment.mockRejectedValue(new Error("file type not allowed"));
    render(<EvidenceAttachments caseId={1} evidenceId={2} canEdit={true} />);
    await screen.findByText("receipt.pdf");

    const file = new File(["hello"], "bad.exe", { type: "application/octet-stream" });
    await user.upload(screen.getByLabelText("Attach file"), file);

    expect(await screen.findByText("file type not allowed")).toBeInTheDocument();
  });
});
