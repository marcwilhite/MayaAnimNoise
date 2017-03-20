# MayaAnimNoise

Custom node for animated noise (random values).
By default random values are generated between -1 and 1 but maybe multiplied by
amplitude and offset attributes.

*Attributes:*  *smoothing* - smooths generated values
            default: 0.5 (range 0 to 1)

            *offset* - offsets generated values -
            default: 0.0

            *amplitude* - multiple to apply to generated values
            default: 1.0

            *frequency* - Multiplies frequency of randomness
            default: 1.0 (range 0 to 1)

            *seed* - value changes random pattern
            default: 1

            *rectify* - Inverts negatives values.
            default: False

            *wave* - Maya optionally generate sine waves instead of noise.
            default: Noise
            output - resulting random values

            *phase* - sets phase of sine wave or offsets frames of noise

*Example:*  
`node = mc.animNoise('myNoseNode')
mc.connectAttr(node+'.out', 'pSphere1.ty')`
