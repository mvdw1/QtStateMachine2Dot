#include <QCoreApplication>
#include <QStateMachine>
#include <QState>
#include <QFinalState>
#include <QTimer>
#include <QDebug>

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);

    QStateMachine machine;

    QStateMachine machine2;
    // Create states
    QState *state1 = new QState();
    QState *state2 = new QState();
    QState *state3 = new QState();


    QState *state4 = new QState();
    QState *state5 = new QState();
    QState *state6 = new QState();

    QFinalState *finalState = new QFinalState();
    QFinalState *finalState2 = new QFinalState();

    // Set state transitions
    state1->addTransition(new QTimer(), &QTimer::timeout, state2);
    state2->addTransition(new QTimer(), &QTimer::timeout, state3);
    state3->addTransition(new QTimer(), &QTimer::timeout, state2);
    state3->addTransition(new QTimer(), &QTimer::timeout, finalState);


    state4->addTransition(new QTimer(), &QTimer::timeout, state5);
    state5->addTransition(new QTimer(), &QTimer::timeout, state4);
    state6->addTransition(new QTimer(), &QTimer::timeout, state5);
    state6->addTransition(new QTimer(), &QTimer::timeout, finalState2);

    // Set state properties
    state1->assignProperty(&app, "state", "State 1");
    state2->assignProperty(&app, "state", "State 2");
    state3->assignProperty(&app, "state", "State 3");

    // Connect state entry signals to slots
    QObject::connect(state1, &QState::entered, []() { qDebug() << "Entered State 1"; });
    QObject::connect(state2, &QState::entered, []() { qDebug() << "Entered State 2"; });
    QObject::connect(state3, &QState::entered, []() { qDebug() << "Entered State 3"; });

    // Add states to the state machine
    machine.addState(state1);
    machine.addState(state2);
    machine.addState(state3);
    machine.addState(finalState);
    machine.setInitialState(state1);

    machine2.addState(state4);
    machine2.addState(state5);
    machine2.addState(state6);
    machine2.addState(finalState2);
    machine2.setInitialState(state4);


    // Start the state machine
    machine.start();

    // Create a timer to trigger state transitions
    QTimer timer;
    timer.setInterval(1000); // 1 second interval
    QObject::connect(&timer, &QTimer::timeout, &machine, &QStateMachine::postEvent);
    timer.start();

    return app.exec();
}\