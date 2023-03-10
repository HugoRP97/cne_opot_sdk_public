class PotProfileListDescriptor:
    def __init__(self, **kwargs):
        # Mandatory values
        self.pot_profile_index = 1
        # If status is True, this means that the Node is a Ingress Node
        self.status = kwargs.get('status', False)
        # If validator is equal to True
        self.validator = kwargs.get('validator', False)
        # Validator key
        # Mandatory for egress Node
        self.validator_key = kwargs.get('validator_key', 0)
        # Prime number used for generating the SSS values
        self.prime_number = kwargs['prime_number']
        # Value of the private polynomial
        self.secret_share = kwargs['secret_share']
        # Public polynomial from the SSS
        self.public_polynomial = kwargs.get('public_polynomial', 0)
        # LPC value from the SSS
        self.lpc = kwargs['lpc']
        # Maintain this constant for the moment
        self.bitmask = kwargs['bitmask']
        # Optional Values that may be set later.
        # Format the masks
        try:
            self.opot_masks = {
                'upstream_mask': kwargs['opot_masks'].get('upstream_mask', None),
                'downstream_mask': kwargs['opot_masks'].get('downstream_mask', None)
            }
            print(self.opot_masks)
        except KeyError:
            self.opot_masks = {'upstream_mask': None, 'downstream_mask': None}
