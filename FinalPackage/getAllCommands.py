import numpy as np
import activateProp
import barrier
from customQP import quadprog
from itertools import combinations
import re
import time
import matrixDijkstra
import copy

class getAllCommands:
    def __init__(self,State,currState,pos,posStart,posRef,t,Ts,input,until):
        self.State = State.State
        self.Conflicts = State.Conflicts
        self.props = State.State.props
        self.accepting_states = State.State.accepting_states
        self.graph = State.State.graph
        self.controllableProp = State.State.controllableProp
        self.uncontrollableProp = State.State.uncontrollableProp
        self.propositions = State.State.propositions
        self.props2Activate = []
        self.currState = []
        self.maxV = State.maxV
        self.hz = int(State.freq)
        self.M = int(State.M)
        self.nom = []
        self.nodeGraph = State.State.nodeGraph
        self.nodes = State.State.nodes
        self.map = State.State.map
        self.State.input = input
        self.State.until = until
        self.bxt_eventually = []
        self.distTotal = np.zeros((1,self.M))[0]
        self.pos = pos.tolist()
        self.Commands(currState,pos,posStart,posRef,t,Ts)

    def trackInputs(self,pos,posStart,posRef,t):
        props = self.props
        self.input = self.State.input[::2].astype(int)
        self.input = self.input[:np.size(self.uncontrollableProp)]

        for i in range(np.size(self.uncontrollableProp)):
            propName = self.uncontrollableProp[i]
            exec('props.' + propName + ' = ' + str(self.input[i]))

        count = 1
        for i in range(np.size(self.State.phi)):
            # Only interested if there is implication
            if self.State.phi[i].implies == 1:
                if int(np.size(self.State.input)) < np.size(self.uncontrollableProp) * 2 + 2 * count:
                    arrayToApp = np.array([0, 0])
                    self.State.input = np.hstack((self.State.input, arrayToApp))

                messTrue = eval(self.State.phi[i].impliesmessage)
                if messTrue and self.State.input[np.size(self.uncontrollableProp) * 2 + 2 * count - 2] == 0:
                    self.State.phi[i].inputTime = t
                    self.State.input[np.size(self.uncontrollableProp) * 2 + 2 * count - 2] = 1
                    self.State.input[np.size(self.uncontrollableProp) * 2 + 2 * count - 1] = t
                elif messTrue and self.State.input[np.size(self.uncontrollableProp) * 2 + 2 * count - 2] == 1:
                    if self.State.input[np.size(self.uncontrollableProp) * 2 + 2 * count - 1] + self.State.phi[i].interval[1] > t:
                        self.State.phi[i].inputTime = self.State.input[np.size(self.uncontrollableProp) * 2 + 2 * count - 1]
                    else:
                        self.State.phi[i].inputTime = t
                        self.State.input[np.size(self.uncontrollableProp) * 2 + 2 * count - 1] = t
                elif not messTrue:
                    self.State.input[np.size(self.uncontrollableProp) * 2 + 2 * count - 2] = 0

                count += 1
        self.props = props
        # Need to reset specs

    def findConditions(self,activate):
        #this is for a pre-failure warning. We want to see what happens if things change with the inputs
        numUncon = np.size(activate.State.uncontrollableProp)
        self.conditions = np.empty((1,numUncon))
        # From your current state, evaluate all possible transitions and find all of the combinations of
        # inputs that are possible
        simpleInput = np.zeros((1, int(np.size(self.State.input) / 2)))
        for i in range(int(np.size(self.State.input) / 2)):
            simpleInput[0, i] = self.State.input[2 * i]
        simpleInput = simpleInput[0][:np.size(self.uncontrollableProp)]
        for i in range(activate.State.State[self.currState].condCNF.__len__()):
            condCNF = activate.State.State[self.currState].condCNF
            for j in range(condCNF[i].__len__()):
                #specVal = np.array([int(s) for line in condCNF[i][j] for s in line.split()])
                specVal = np.array(condCNF[i][j])
                # We are only interested in the uncontrollable propositions (inputs)
                specVal = specVal[0:numUncon]
                canAppend = 0
                for j in range(np.size(np.where(simpleInput == 1)[0])):
                    if np.size(np.where(simpleInput == 1)[0]) <= np.size(np.where(specVal == 1)[0]):
                        locOfInp = np.where(specVal == 1)[0]
                        if np.size(locOfInp) != 0:
                            ind = simpleInput[np.where(specVal == 1)[0][j]]
                            if int(ind) == 1:
                                canAppend += 1
                if canAppend == np.size(np.where(simpleInput == 1)[0]):
                    self.conditions = np.vstack((self.conditions, specVal))

        # The first row is zero because of how we appended. Also, we only want the unique values to increase speed
        self.conditions = self.conditions.astype(int)
        self.conditions = self.conditions[1:,:]
        self.conditions = np.unique(self.conditions, axis = 0)
        # for i in range(np.size(simpleInput)):
        #     if simpleInput[i] == 1:
        #         indOfMatch = np.where(self.conditions[:,i] == 1)[0]
        #         self.conditions = np.delete(self.conditions,indOfMatch,axis=0)

    def potentialConflicts(self,act,pos,posRef,ub,t):
        # Lets check things that can be activated for each robot
        # These are the indexes of the inputs for the robot
        badConditions = []
        robustRef = []
        while np.size(self.conditions,0) > 0:
            try:
                activate = activateProp.activateProp.activate(act, self.currState, self.conditions[0], pos, posRef, t,1)
                if len(activate.robustness) > 0:
                    if any(x < 0 for x in activate.robustness):
                        badConditions.append(self.conditions[0])
                        robustRef.append(activate.robustness)
                        actInd = np.where(self.conditions[0]==1)[0]
                        indToDel = []
                        for i in range(np.size(actInd)):
                            indToDel.extend(np.where(self.conditions[:, actInd[i]] == 1)[0].tolist())
                        indToDel = np.unique(indToDel)
                        if np.size(self.conditions, 0) > 0:
                            self.conditions = np.delete(self.conditions, indToDel, 0)
                if np.size(self.conditions, 0) > 0:
                    self.conditions = np.delete(self.conditions,0,0)
            except Exception as e:
                if np.size(self.conditions,0) > 0:
                    self.conditions = np.delete(self.conditions,0,0)
                pass
        # for i in range(np.size(self.conditions, 0)):
        #     try:
        #         activate = activateProp.activateProp.activate(act, self.currState, self.conditions[i], pos, posRef, t,1)
        #         if len(activate.robustness) > 0:
        #             if any(x < 0 for x in activate.robustness):
        #                 badConditions.append(self.conditions[i])
        #                 robustRef.append(activate.robustness)
        #     except:
        #         pass
        # the badConditions variable shows which combinations of inputs result in a negative robustness score
        # for a proposition
        currInput = self.State.input[::2].astype(int)
        currInput = currInput[:np.size(self.uncontrollableProp)]
        locOfCurrent = np.where(currInput == 1)[0]
        for i in range(np.size(badConditions, 0)):
            locOfTrue = np.where(badConditions[i] == 1)[0]
            msg = 'If '
            if not np.array_equal(locOfCurrent, locOfTrue):
                for j in range(np.size(locOfTrue)):
                    if j == np.size(locOfTrue) - 1:
                        msg += 'and ' + self.uncontrollableProp[locOfTrue[j]] + ' '
                    else:
                        msg += self.uncontrollableProp[locOfTrue[j]] + ', '
                if np.size(locOfTrue) == 1:
                    msg += 'is sensed now, the specification may be violated'
                else:
                    msg += 'are sensed now, the specification may be violated'

            indOfNeg = np.where(np.asarray(robustRef[i]) < 0)[0]
            for j in range(np.size(indOfNeg)):
                phiId = activate.ids[indOfNeg[j]]
                timeNeeded = round(-1*robustRef[i][indOfNeg[j]]/activate.weights[1],2)
                msg += '. To make robustness positive the task ' + self.State.phi[phiId].params + ' needs ' + str(timeNeeded) + ' more seconds to be completed'
            print(msg)

    def evalProps(self,pos,posRef,t):
        props = self.props
        # Find the values of all parameters
        if self.State.wall is not None and len(self.State.wall) != 0:
            wall = self.State.wall
            valuesOfControl = eval(','.join(self.State.parameters), {'__builtins__': None},
                                    {'pos': pos, 'np': np, 'posRef': posRef, 'wall': wall})
        else:
            wall = []
            valuesOfControl = eval(','.join(self.State.parameters), {'__builtins__': None},
                                    {'pos': pos, 'np': np, 'posRef': posRef})
        # change from true/false to 1/0
        valuesOfControl = np.multiply(valuesOfControl,1)

        # Assign all for the values to the propositions
        for i in range(np.size(self.controllableProp)):
            propName = self.controllableProp[i]
            exec('props.' + propName + ' = ' + str(valuesOfControl[i]))

        for i in range(len(self.State.phi)):
            if self.State.phi[i].type == 'alw':
                if isinstance(self.State.phi[i].inputTime,float):
                    inputTime = self.State.phi[i].inputTime
                else:
                    inputTime = 0
                if t < self.State.phi[i].interval[0] + inputTime or t > self.State.phi[i].interval[1] + inputTime:
                    propName = self.State.phi[i].prop_label
                    exec('props.' + propName + ' = ' '1')
                if t > self.State.phi[i].interval[0] +inputTime and t < self.State.phi[i].interval[1] + inputTime:
                    propName = self.State.phi[i].prop_label
                    if not eval('props.' + propName) and self.State.phi[i].until == 0:
                        raise Exception('SPECIFICATION VIOLATED: PARAMETER: {}, ACTUAL VALUE: {}, PROP LABEL: {}'
                                        .format(self.State.phi[i].params, eval(self.State.phi[i].funcOf),self.State.phi[i].prop_label))
            dir = re.findall('(?=\().+?(?=\*)', self.State.phi[i].funcOf)
            dir[0] = re.findall('(?<=\().+(?<=\))', dir[0])[0]
            dir[1] = re.findall('(?=\().+(?<=\))', dir[1])[0]
            vals = [-eval(elem, {'__builtins__': None}, {'pos': pos, 'np': np, 'posRef': posRef, 'wall':wall}) for elem in dir]
            self.State.phi[i].nom[1, 0:2] = vals
            #Need to reset the point in case it needs to be evaluated
            dirRef = self.State.phi[i].dir
            self.State.phi[i].point = []
            for j in range(len(dirRef)):
                try:
                    self.State.phi[i].point.append(-1 * float(re.search('(?=(\+|\-)).+(?=$)', dirRef[j])[0]))
                except:
                    try:
                        self.State.phi[i].point.append(re.search('(?=posRef\[).+(?<=\])', dirRef[j])[0])
                    except:
                        pass
            self.State.phi[i].point = np.asarray(self.State.phi[i].point)

            try:
                if not isinstance(self.State.phi[i].point[0], float):
                    self.State.phi[i].point = [eval(self.State.phi[i].point[0]), eval(self.State.phi[i].point[1])]
            except:
                pass
            self.State.phi[i].currentTruth = eval('props.' + self.State.phi[i].prop_label, {'__builtins__': None},
                                 {'props': props})

            if self.State.phi[i].currentTruth:
                nomR = np.zeros((1, 3), dtype=float)[0]
                cost = eval(self.State.phi[i].funcOf)
                signF = -self.State.phi[i].signFS[0]
                self.State.phi[i].distFromSafe = cost + signF * self.State.phi[i].p
            else:
                nomR, cost = self.getNom(self.State.phi[i], pos, posRef)
                signF = self.State.phi[i].signFS[0]
                self.State.phi[i].distFromSafe = cost + signF * self.State.phi[i].p
                rob = self.State.phi[i].robotsInvolved[0]
                self.State.phi[i].time2Finish = cost / self.maxV[3 * rob - 3]
            self.State.phi[i].nom[1, :] = nomR

        self.props = props

    def Commands(self,currState,pos,posStart,posRef,t,Ts):
        # bounds for commands
        lb = -self.maxV
        ub = self.maxV
        wall = self.State.wall
        # Go through all specifications and, if there is implication, log the time that the input became activated.
        # also, if a specification has been satisfied, the input should be reset.
        self.trackInputs(pos, posStart, posRef,t)
        # Evaluate the current state of the environment
        self.evalProps(pos, posRef, t)
        #Find Propositions to activate based on the current state and transitiosn to an accepting state
        act = activateProp.activateProp(self, 0, [],self.input,self.getNom)
        activate = activateProp.activateProp.activate(act,currState,[],pos,posRef,t,0)

        print(activate.props2Activate)
        self.props2Activate = activate.props2Activate
        self.currState = activate.currState
        # Toggle to turn on/off pre failure warnings
        preFailure = 0
        if preFailure:
            # this is for a pre-failure warning. We want to see what happens if things change with the inputs
            self.findConditions(activate)

            # Check for potential conflicts if additional inputs are sensed
            self.potentialConflicts(act,pos, posRef, ub, t)
        # create the new STL specification with the activated propositions
        ia = [list(self.State.controllableProp).index(s) for s in list(self.props2Activate)]
        phiIndex = [self.State.controllablePropOrder[s] for s in ia]
        phi = [self.State.phi[s] for s in phiIndex]

        # loop through find the order of the stl objects for assignment later
        orderOfPhi = []
        for i in range(np.size(phi)):
            orderOfPhi.append(phi[i].id)

        nom = np.zeros((1,3 * self.M))

        for i in range(1,self.M+1):
            # Find all fo the specifications for each robot
            phiRobot = []
            ids = []
            for j in range(np.size(phi)):
                if np.where(phi[j].robotsInvolved==i)[0].size != 0:
                    phiRobot.append(phi[j])
                    ids.append(phi[j].id)

            if phiRobot != []:
                # find the candidate barrier function at the position and find partial derivatives
                bxtx, phiRobotPlace, propsActivated, bxt_eventually = barrier.barrier(self, pos, posStart, posRef, t,
                                                                                      Ts, phiRobot, 100, self.hz,wall,0)

                phiRobot = []
                ids = []
                for j in range(np.size(phiRobotPlace)):
                    try:
                        if phiRobotPlace[j].bxt_i != 0:
                            phiRobot.append(phiRobotPlace[j])
                            ids.append(phiRobotPlace[j].id)
                    except:
                        pass

                self.bxt_eventually.append(bxt_eventually)

                [bPartialX, bPartialT] = barrier.partials(self, pos, posStart, posRef, t, Ts, phiRobot, 100, self.hz,
                                                          bxtx,wall)

                A = -1 * np.dot(np.array(bPartialX), np.identity(3 * self.M))
                if abs(bPartialT[0]) > 50:
                    bPartialT[0] = 0

                alpha = 1
                b = alpha * (bxtx) + bPartialT[0]
                # check for changes.these are the robots affected by barrier functions
                if np.any(bPartialX):
                    nominals = np.empty((1, 3), dtype=float)
                    for j in range(np.size(phiRobot)):
                        if np.sum(abs(phiRobot[j].nom[1, :])) != 0:
                            velBound = ub[phiRobot[j].nom[0, 0:].astype(int)]
                            thisNom = phiRobot[j].nom
                            normalize = np.sqrt(thisNom[1, 0] ** 2 + thisNom[1, 1] ** 2)
                            thisNomBounded = np.zeros((1, 3))[0]
                            if normalize != 0:
                                thisNomBounded[0:2] = np.multiply((thisNom[1, 0:2] / normalize), velBound[0:2])
                            else:
                                thisNomBounded = thisNom[1, :]

                            nominals = np.vstack((nominals, thisNom[0, :], thisNomBounded))
                            # break
                    nominals = nominals[1:, :]

                    # This is to check if there are multiple nominal controllers (2+ activated cbfs for same robot)
                    if np.size(nominals, 0) > 2:
                        for j in range(int(np.size(nominals, 0) / 2)):
                            if j > 0:
                                nominals = np.delete(nominals, 2, 0)
                        finalT = []
                        typeOf = []
                        for j in range(np.size(phiRobot)):
                            if phiRobot[j].implies == 0:
                                finalT.append(phiRobot[j].interval[1])
                            else:
                                finalT.append(phiRobot[j].interval[1] + phiRobot[j].inputTime)
                            typeOf.append(phiRobot[j].type)
                        try:
                            if np.all(finalT == finalT[0]):
                                locOfSoonest = typeOf.index('ev')
                            else:
                                locOfSoonest = np.argmin(finalT)
                        except:
                            locOfSoonest = np.argmin(finalT)
                        try:
                            nominals = np.vstack((nominals[0,:],nominals[locOfSoonest+1,:]))
                        except:
                            pass
                        #print('multiple nominal controllers. Attempting to satisfy specification by satisfying in order of time bound')

                    Anew = A[3 * i - 3:3 * i]
                    lbI = lb[3 * i - 3:3 * i]
                    ubI = ub[3 * i - 3:3 * i]
                    if np.any(nominals):
                        x0 = nominals[1,:]
                    else:
                        x0 = np.array([0,0,0])
                        nominals = np.zeros((2, 3))

                    H = np.array([[2,0,0],[0,2,0],[0,0,2]])
                    f = np.array([-2*nominals[1,0],-2*nominals[1,1],-2*nominals[1,2]]).T

                    qp = quadprog(H,f,Anew, b, x0, lbI, ubI)
                    nomInd = qp.result.x

                    if not qp.result.success:
                        print('Specification violated')
                        nom[0][3 * i - 3] = 0
                        nom[0][3 * i - 2] = 0
                        nom[0][3 * i - 1] = 0
                    else:
                        nom[0][3 * i - 3] = nomInd[0]
                        nom[0][3 * i - 2] = nomInd[1]
                        nom[0][3 * i - 1] = nomInd[2]
        self.nom = nom

    def getNom(self,phi, pos, nom):
        avoidWallsInPath = 0
        wallDistance = .05
        startPos = pos[3*(phi.robotsInvolved[0]-1):3 * (phi.robotsInvolved[0] - 1) + 2]
        canReach = 0
        isect = self.intersectPoint(phi.point[0], phi.point[1], startPos[0], startPos[1],
                                self.State.map[:, 0], self.State.map[:, 1], self.State.map[:, 2], self.State.map[:, 3])

        if not np.any(isect):
            dist2closest1 = self.distWall(startPos, phi.point, np.vstack((self.State.map[:, 0:2],self.State.map[:, 2:4])))
            if min(dist2closest1) > wallDistance:
                canReach = 1

        if canReach == 0:
            # Find the closest nodes to the goal
            dist2p = np.sqrt((phi.point[0] - self.State.nodes[:, 0]) ** 2 +
                                      (phi.point[1] - self.State.nodes[:, 1]) ** 2)
            idx = np.argsort(dist2p)

            # Connect goal to first node it can. starting with closest
            isect = self.intersectPointVec(phi.point[0], phi.point[1], self.State.nodes[idx, 0],self.State.nodes[idx, 1],
                                        self.State.map[:, 0], self.State.map[:, 1], self.State.map[:, 2],self.State.map[:, 3])
            closestGoalInd = idx[isect]

            if avoidWallsInPath:
                iToDel = []
                for i in range(np.size(closestGoalInd)):
                    dist2Walls = self.distWall(phi.point, self.State.nodes[closestGoalInd[i],:],
                                               np.vstack((self.State.map[:,0:2],self.State.map[:,2:4])))
                    if min(dist2Walls) < wallDistance:
                        iToDel.append(i)
                closestGoalInd = np.delete(closestGoalInd,iToDel)

            closestGoalInd = closestGoalInd[0]
            closestGoal = self.State.nodes[closestGoalInd]

            # Find the closest nodes to the start
            dist2p2 = np.sqrt((startPos[0]-self.State.nodes[:, 0]) ** 2 + (startPos[1] - self.State.nodes[:, 1]) ** 2)
            idx = np.argsort(dist2p2)

            isect = self.intersectPointVec(startPos[0], startPos[1], self.State.nodes[idx, 0],self.State.nodes[idx, 1],
                                self.State.map[:, 0], self.State.map[:, 1], self.State.map[:, 2],self.State.map[:, 3])
            closestStartInd = idx[isect]
            closestStartDist = np.sqrt((startPos[0] - self.State.nodes[closestStartInd,0]) ** 2 +
                                       (startPos[1] - self.State.nodes[closestStartInd,1]) ** 2)

            if avoidWallsInPath:
                iToDel = []
                for i in range(np.size(closestStartInd)):
                    dist2Walls = self.distWall(startPos, self.State.nodes[closestStartInd[i],:],
                                               np.vstack((self.State.map[:,0:2],self.State.map[:,2:4])))
                    if min(dist2Walls) < wallDistance:
                        iToDel.append(i)
                closestStartInd = np.delete(closestStartInd,iToDel)
                closestStartDist = np.delete(closestStartDist,iToDel)

            # Find Route
            # minDist = []
            # for i in range(np.size(closestStartInd,0)):
            #     closStart = self.State.nodes[closestStartInd[i]]
            #     costToStart = np.sqrt((closStart[0] - startPos[0]) ** 2 + (closStart[1] - startPos[1]) ** 2)
            #     minDist.append(costToStart + self.State.nodeConnections[closestStartInd[i]][closestGoalInd][-1])

            nodesToGo = [self.State.nodeConnections[i][closestGoalInd][-1] for i in closestStartInd]
            distToGoals = np.asarray(nodesToGo) + np.asarray(closestStartDist)
            if np.size(distToGoals) != 0:
                indOfNext = np.argmin(distToGoals)
                wayPoint = self.State.nodes[closestStartInd[indOfNext],:]
                nom = wayPoint - startPos
                nom = np.hstack((nom,0))
                closestStart = self.State.nodes[closestStartInd[indOfNext]]
                costToStart = np.sqrt((closestStart[0] - startPos[0]) ** 2 + (closestStart[1] - startPos[1]) ** 2)
                costToGoal = np.sqrt((phi.point[0] - closestGoal[0]) ** 2 + (phi.point[1] - closestGoal[1]) ** 2)
                pathCost = self.State.nodeConnections[closestStartInd[indOfNext]][closestGoalInd][-1]

                cost = costToStart + costToGoal + pathCost
        else:
            nom = phi.point - startPos
            nom = np.hstack((nom, 0))
            cost = np.sqrt((phi.point[0] - startPos[0]) ** 2 + (phi.point[1] - startPos[1]) ** 2)

        return nom, cost

    # def intersectPoint(self, x1, y1, x2, y2, x3, y3, x4, y4):
    #     ua = np.divide(((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)), ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)))
    #     ub = np.divide(((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)), ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)))
    #
    #     isect = (ua>=0)*(ub>=0)*(ua<=1)*(ub<=1)
    #     return isect
    #
    # def intersectPointVec(self, x1, y1, x2, y2, x3, y3, x4, y4):
    #     with np.errstate(divide='ignore', invalid='ignore'):
    #         denom = np.outer((x2 - x1),(y4 - y3)) - np.outer((y2 - y1),(x4 - x3))
    #
    #         ua = np.divide(((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)), denom)
    #         ub = (np.outer((x2 - x1), (y1 - y3)) - np.outer((y2 - y1), (x1 - x3)))/ denom
    #
    #         isect = (ua>=0)*(ub>=0)*(ua<=1)*(ub<=1)
    #         isect = np.any(isect, axis=1)
    #         isect = np.where(isect == False)[0]
    #         return isect

    # def distWall(self, p1, p2, pt):
    #     with np.errstate(divide='ignore', invalid='ignore'):
    #         dx = p2[0] - p1[0]
    #         dy = p2[1] - p1[1]
    #
    #         t = ((pt[:,0] - p1[0]) * dx + (pt[:,1] - p1[1]) * dy) / (dx ** 2 + dy ** 2)
    #
    #         if dx == 0 and dy == 0:
    #             closestP = p1
    #             dx = pt[0] - p1[0]
    #             dy = pt[1] - p1[1]
    #             dist = np.zeros((1,np.size(pt,0)))[0]
    #             # dist = np.sqrt(dx ** 2 + dy ** 2) * np.ones((1,np.size(pt,0)))[0]
    #         else:
    #             dist = np.zeros((1,np.size(pt,0)))[0]
    #
    #         try:
    #             indL = np.where(t<0)[0]
    #             dx = pt[indL,0] - p1[0]
    #             dy = pt[indL,1] - p1[1]
    #             dist[indL] = np.sqrt(dx ** 2 + dy ** 2)
    #         except:
    #             pass
    #
    #         try:
    #             indG = np.where(t>0)[0]
    #             dx = pt[indG,0] - p1[0]
    #             dy = pt[indG,1] - p1[1]
    #             dist[indG] = np.sqrt(dx ** 2 + dy ** 2)
    #         except:
    #             pass
    #
    #         try:
    #             indM = np.where((t >= 0) & (t <= 1))[0]
    #             dx = p2[0] - p1[0]
    #             dy = p2[1] - p1[1]
    #             closestP = np.array([p1[0] + t[indM] * dx, p1[1] + t[indM] * dy])
    #             dx = pt[indM,0] - closestP[0]
    #             dy = pt[indM,1] - closestP[1]
    #             dist[indM] = np.sqrt(dx ** 2 + dy ** 2)
    #         except:
    #             pass
    #
    #         return dist
