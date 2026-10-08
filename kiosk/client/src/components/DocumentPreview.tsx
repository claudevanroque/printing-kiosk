import type {LocalDocument,} from "../types/localDocument";

import {getDocumentPreviewUrl,} from "../services/documentApi";


interface Props {
    document: LocalDocument;

    onRemove: () => void;
    onContinue: () => void;
}


export default function DocumentPreview({
    document,
    onRemove,
    onContinue,
}: Props) {

    const previewUrl =
        getDocumentPreviewUrl(
            document.id
        );

    const fileSizeMb =
        (
            document.file_size /
            1024 /
            1024
        ).toFixed(2);


    return (
        <div className="document-preview">

            <div className="preview-header">
                <h2>
                    Document Preview
                </h2>
            </div>


            <div className="preview-layout">

                <div className="preview-frame">

                    {document.content_type ===
                    "application/pdf" ? (

                        <iframe
                            src={`${previewUrl}#toolbar=0&navpanes=0&scrollbar=0&view=FitH`}
                            title="Document preview"
                        />

                    ) : (

                        <img
                            src={previewUrl}
                            alt="Document preview"
                        />

                    )}

                </div>


                <div className="document-info">

                    <h3>
                        {
                            document
                                .original_filename
                        }
                    </h3>


                    <p>
                        Pages:
                        {" "}
                        <strong>
                            {document.page_count}
                        </strong>
                    </p>


                    <p>
                        Size:
                        {" "}
                        <strong>
                            {fileSizeMb} MB
                        </strong>
                    </p>


                    <p>
                        Source:
                        {" "}
                        <strong>
                            {document.source}
                        </strong>
                    </p>

                </div>

            </div>


            <div className="preview-actions">

                <button
                    type="button"
                    className="secondary-button"
                    onClick={onRemove}
                >
                    Remove
                </button>


                <button
                    type="button"
                    className="primary-button"
                    onClick={onContinue}
                >
                    Continue
                </button>

            </div>

        </div>
    );
}