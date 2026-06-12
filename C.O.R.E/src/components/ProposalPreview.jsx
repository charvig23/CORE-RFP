import html2pdf from "html2pdf.js";

function ProposalPreview({ html }) {
  if (!html) return null;

  const download = () => {
    html2pdf().from(html).save("proposal.pdf");
  };

  return (
    <div className="card">
      <h3>📄 Final Proposal</h3>

      <div
        className="proposal-box"
        dangerouslySetInnerHTML={{ __html: html }}
      />

      <button onClick={download}>⬇ Download Proposal</button>
    </div>
  );
}

export default ProposalPreview;
