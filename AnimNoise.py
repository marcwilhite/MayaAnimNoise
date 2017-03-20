import sys
import random
import maya.api.OpenMaya as om
import maya.cmds as mc
import math


def maya_useNewAPI():
    pass


kPluginNodeName = "animNoise"
kPluginNodeId = om.MTypeId(0x001250ff)

kNameFlag = "-n"
kNameLongFlag = "-name"


class AnimNoise(om.MPxNode):
    """
    Custom node for animated noise (random values).
    By default random values are generated between -1 and 1 but maybe multiplied by
    amplitude and offset attributes.

     Attributes:  smoothing - smooths generated values
                    default: 0.5 (range 0 to 1)

                  offset - offsets generated values -
                    default: 0.0

                  amplitude - multiple to apply to generated values
                    default: 1.0

                  frequency - Multiplies frequency of randomness
                    default: 1.0 (range 0 to 1)

                  seed - value changes random pattern
                    default: 1

                  rectify - Inverts negatives values.
                    default: False

                  wave - Maya optionally generate sine waves instead of noise.
                    default: Noise
                  output - resulting random values

                  phase - sets phase of sine wave or offsets frames of noise

        Example:  node = mc.animNoise('myNoseNode')
                  mc.connectAttr(node+'.out', 'pSphere1.ty')

=============================================================================== """

    time = om.MObject()
    smoothing = om.MObject()
    output = om.MObject()

    @staticmethod
    def creator():
        return AnimNoise()

    @staticmethod
    def initialize():
        unitAttr = om.MFnUnitAttribute()
        AnimNoise.time = unitAttr.create("time", "tm", om.MFnUnitAttribute.kTime, 0.0)

        nAttr = om.MFnNumericAttribute()
        AnimNoise.smoothing = nAttr.create("smoothing", "smooth", om.MFnNumericData.kFloat, 0.5)
        nAttr.setMin(0)
        nAttr.setMax(1)
        nAttr.storable = True
        nAttr.keyable = True

        AnimNoise.offset = nAttr.create("offset", "off", om.MFnNumericData.kFloat, 0.0)
        nAttr.storable = True
        nAttr.keyable = True

        AnimNoise.amplitude = nAttr.create("amplitude", "amp", om.MFnNumericData.kFloat, 1.0)
        nAttr.storable = True
        nAttr.keyable = True

        AnimNoise.frequency = nAttr.create("frequency", "frequency", om.MFnNumericData.kFloat, 0.25)
        nAttr.setMin(0)
        nAttr.setMax(1)
        nAttr.storable = True
        nAttr.keyable = True

        AnimNoise.seed = nAttr.create("seed", "seed", om.MFnNumericData.kInt, 1)
        nAttr.storable = True

        AnimNoise.smoothIter = nAttr.create("smoothIterations", "smiter", om.MFnNumericData.kInt, 100)
        nAttr.storable = True

        AnimNoise.output = nAttr.create("output", "out", om.MFnNumericData.kFloat, 0.0)
        nAttr.writable = True

        AnimNoise.rectify = nAttr.create("rectify", "rect", om.MFnNumericData.kBoolean, False)
        nAttr.storable = True
        nAttr.keyable = True

        AnimNoise.phase = nAttr.create("phase", "p", om.MFnNumericData.kFloat, 0.0)
        nAttr.storable = True
        nAttr.keyable = True

        enumAttr = om.MFnEnumAttribute()
        AnimNoise.wave = enumAttr.create("wave", "wav")
        enumAttr.addField("Noise", 0)
        enumAttr.addField("Sine", 1)
        enumAttr.storable = True
        enumAttr.keyable = True

        AnimNoise.addAttribute(AnimNoise.time)
        AnimNoise.addAttribute(AnimNoise.offset)
        AnimNoise.addAttribute(AnimNoise.amplitude)
        AnimNoise.addAttribute(AnimNoise.frequency)
        AnimNoise.addAttribute(AnimNoise.smoothIter)
        AnimNoise.addAttribute(AnimNoise.output)
        AnimNoise.addAttribute(AnimNoise.rectify)
        AnimNoise.addAttribute(AnimNoise.wave)
        AnimNoise.addAttribute(AnimNoise.phase)
        AnimNoise.addAttribute(AnimNoise.smoothing)
        AnimNoise.addAttribute(AnimNoise.seed)

        AnimNoise.attributeAffects(AnimNoise.smoothing, AnimNoise.output)
        AnimNoise.attributeAffects(AnimNoise.time, AnimNoise.output)
        AnimNoise.attributeAffects(AnimNoise.offset, AnimNoise.output)
        AnimNoise.attributeAffects(AnimNoise.amplitude, AnimNoise.output)
        AnimNoise.attributeAffects(AnimNoise.seed, AnimNoise.output)
        AnimNoise.attributeAffects(AnimNoise.smoothIter, AnimNoise.output)
        AnimNoise.attributeAffects(AnimNoise.frequency, AnimNoise.output)
        AnimNoise.attributeAffects(AnimNoise.rectify, AnimNoise.output)
        AnimNoise.attributeAffects(AnimNoise.wave, AnimNoise.output)
        AnimNoise.attributeAffects(AnimNoise.phase, AnimNoise.output)

    def __init__(self):
        om.MPxNode.__init__(self)
        self.smoother = Smoother()
        self.previousValue = 0

    def compute(self, plug, data):
        if plug == AnimNoise.output:
            timeData = data.inputValue(AnimNoise.time)
            tempTime = timeData.asTime()
            frame = int(tempTime.value)

            smoothData = data.inputValue(AnimNoise.smoothing)
            smoothing = smoothData.asFloat()
            if not smoothing:
                smoothing = 0.01

            offsetData = data.inputValue(AnimNoise.offset)
            offset = offsetData.asFloat()

            ampData = data.inputValue(AnimNoise.amplitude)
            amp = ampData.asFloat()

            seedData = data.inputValue(AnimNoise.seed)
            seed = seedData.asInt()

            frequencyData = data.inputValue(AnimNoise.frequency)
            frequency = frequencyData.asFloat()

            smoothIterData = data.inputValue(AnimNoise.smoothIter)
            smoothIter = smoothIterData.asInt()

            phase = data.inputValue(AnimNoise.phase).asFloat()

            doSine = data.inputValue(AnimNoise.wave)

            if doSine.asInt():
                angle = om.MAngle()
                angle.unit = om.MAngle.kDegrees
                angle.value = phase
                result = math.sin(angle.asRadians() + (frame * frequency * math.pi * 2))

            else:
                fraction = float(frame * frequency) % 1.0
                fraction = (1.0 - math.cos(fraction * math.pi * 0.5) + fraction) * 0.5
                frame = int(frame * frequency)
                seed += int(phase)

                self.smoother.setAmount(smoothing * 0.95, iters=smoothIter)
                current, previous = self.smoother.process(frame + seed)

                result = (previous * (1.0 - fraction)) + (current * fraction)

            result *= amp
            doRectify = data.inputValue(AnimNoise.rectify)
            if doRectify.asBool():
                result = abs(result)

            result += offset

            outHandle = data.outputValue(AnimNoise.output)
            outHandle.setFloat(result)
            data.setClean(plug)
        else:
            return om.kUnknownParameter


class makeAnimNoiseCmd(om.MPxCommand):
    @staticmethod
    def cmdCreator():
        return makeAnimNoiseCmd()

    def isUndable(self):
        return True

    def hasSyntax(self):
        return True

    @staticmethod
    def commandSyntax():
        syntax = om.MSyntax()
        syntax.addArg(om.MSyntax.kString)
        syntax.addFlag(kNameFlag, kNameLongFlag, om.MSyntax.kString)
        return syntax

    def doIt(self, args):
        self.name = "animNoise"
        argData = om.MArgDatabase(self.syntax(), args)

        if argData.isFlagSet(kNameFlag):
            self.name = argData.flagArgumentString(kNameFlag, 0)

        if len(args):
            self.target = argData.commandArgumentString(0)
            if not (len(self.target.split('.')) == 2 and mc.objExists(self.target)):
                self.displayWarning(self.target + ' does not exist!')
                self.target = None
        else:
            self.target = None

        self.redoIt()

    def redoIt(self):
        self.node = mc.createNode('animNoise')
        self.node = mc.rename(self.node, self.name)
        mc.connectAttr('time1.outTime', self.node + '.time')

        if self.target:
            mc.connectAttr(self.node + '.output', self.target, force=True)
            mc.select(self.target, r=True)

        self.setResult(self.node)

    def undoIt(self):
        mc.delete(self.node)


# initialize the script plug-in
def initializePlugin(obj):
    mplugin = om.MFnPlugin(obj)
    try:
        mplugin.registerNode(kPluginNodeName, kPluginNodeId, AnimNoise.creator, AnimNoise.initialize)
    except:
        sys.stderr.write("Failed to register node: %s" % kPluginNodeName)
        raise

    try:
        mplugin.registerCommand("animNoise", makeAnimNoiseCmd.cmdCreator, makeAnimNoiseCmd.commandSyntax)
    except:
        sys.stderr.write("Failed to register command\n")
        raise


# uninitialize the script plug-in
def uninitializePlugin(obj):
    mplugin = om.MFnPlugin(obj)
    try:
        mplugin.deregisterNode(kPluginNodeId)
    except:
        sys.stderr.write("Failed to deregister node: %s" % kPluginNodeName)
        raise

    try:
        mplugin.deregisterCommand("animNoise")
    except:
        sys.stderr.write("Failed to deregister command\n")
        raise


class Smoother(object):
    ''' Simple class for smoothing key/curve data '''
    def __init__(self):
        self.a = 0.9
        self.b = 1.0 - self.a
        self.iters = 100

    def process(self, seed):
        random.seed(seed - (self.iters + 1))
        value = random.random()
        prev = 0
        for i in range(seed - self.iters, seed):
            prev = value
            random.seed(i)
            value = (random.random() * self.b) + (value * self.a)
        value = (value * 2) - 1.0
        prev = (prev * 2) - 1.0
        return (value, prev)

    def setAmount(self, amount, iters=100):
        self.a = amount
        self.b = 1.0 - self.a
        self.iters = iters
