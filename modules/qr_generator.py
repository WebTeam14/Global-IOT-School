import qrcode


def generate_qr_code(data, output_path):
    """
    Creates a QR code image encoding the given text/URL,
    and saves it as a PNG file at output_path.
    """

    qr = qrcode.QRCode(
        version=1,          # controls the size/complexity of the QR grid; 1 = smallest
        box_size=10,        # size of each little square in the QR code, in pixels
        border=2            # thickness of the white border around the QR code
    )

    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)

    return output_path